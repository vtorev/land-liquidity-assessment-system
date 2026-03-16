"""
FastAPI приложение для системы оценки ликвидности земельных участков
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
import redis
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from shapely.geometry import shape, Polygon
import geopandas as gpd

from src.models import CadastreParcel, ParcelFeature, LiquidityAssessment
from src.data_acquisition.cadastre_parser import RosreestrParser
from src.feature_engineering.feature_calculator import FeatureCalculator
from src.ml.liquidity_model import LiquidityAssessmentService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройка FastAPI
app = FastAPI(
    title="Land Liquidity Assessment API",
    description="API для оценки ликвидности земельных участков ИЖС",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене нужно ограничить
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка базы данных
DATABASE_URL = "postgresql://user:password@localhost:5432/land_liquidity"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Настройка Redis для кэширования
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Pydantic модели для API


class ParcelRequest(BaseModel):
    """Запрос на оценку участка"""
    cadastral_number: Optional[str] = Field(None, description="Кадастровый номер участка")
    latitude: Optional[float] = Field(None, description="Широта центра участка")
    longitude: Optional[float] = Field(None, description="Долгота центра участка")
    address: Optional[str] = Field(None, description="Адрес участка")


class ParcelInfo(BaseModel):
    """Информация об участке"""
    id: int
    cadastral_number: str
    area: Optional[float]
    area_unit: Optional[str]
    category: Optional[str]
    permitted_use: Optional[str]
    address: Optional[str]
    centroid_lat: Optional[float]
    centroid_lon: Optional[float]
    created_at: datetime


class LiquidityAssessmentResponse(BaseModel):
    """Результат оценки ликвидности"""
    parcel_id: int
    cadastral_number: str
    liquidity_score: float
    liquidity_category: str
    predicted_price: Optional[float]
    confidence_interval: Optional[Dict[str, float]]
    assessment_date: datetime
    explanation: Dict[str, Any]
    factors: List[Dict[str, Any]]


class FeatureResponse(BaseModel):
    """Признаки участка"""
    feature_type: str
    feature_name: str
    feature_value: Optional[float]
    feature_text: Optional[str]
    calculation_method: Optional[str]


# Зависимости


def get_db():
    """Зависимость для получения сессии базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_redis():
    """Зависимость для получения Redis клиента"""
    return redis_client


# Маршруты API


@app.get("/")
async def root():
    """Корневой маршрут"""
    return {"message": "Land Liquidity Assessment API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса"""
    try:
        # Проверка подключения к базе данных
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # Проверка Redis
        redis_client.ping()
        
        return {
            "status": "healthy",
            "database": "connected",
            "redis": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@app.post("/parcels/search", response_model=ParcelInfo)
async def search_parcel(
    request: ParcelRequest,
    db: Session = Depends(get_db),
    cache: redis.Redis = Depends(get_redis)
):
    """
    Поиск участка по кадастровому номеру, координатам или адресу
    """
    cache_key = f"parcel_search:{hash(str(request.dict()))}"
    
    # Проверка кэша
    cached_result = cache.get(cache_key)
    if cached_result:
        return JSONResponse(content=json.loads(cached_result))
    
    parser = RosreestrParser()
    parcel_data = None
    
    # Поиск по кадастровому номеру
    if request.cadastral_number:
        parcel_data = parser.get_parcel_by_cadastral_number(request.cadastral_number)
    # Поиск по координатам
    elif request.latitude and request.longitude:
        parcel_data = parser.get_parcel_by_coordinates(request.latitude, request.longitude)
    else:
        raise HTTPException(status_code=400, detail="Необходимо указать кадастровый номер или координаты")
    
    if not parcel_data:
        raise HTTPException(status_code=404, detail="Участок не найден")
    
    # Сохранение в базу данных
    from src.models import CadastreParcel as DBParcel
    db_parcel = DBParcel(
        cadastral_number=parcel_data.cadastral_number,
        area=parcel_data.area,
        area_unit=parcel_data.area_unit,
        category=parcel_data.category,
        permitted_use=parcel_data.permitted_use,
        address=parcel_data.address,
        cadastral_block=parcel_data.cadastral_block,
        source=parcel_data.source,
        source_id=parcel_data.source_id,
        coordinates=parcel_data.coordinates.wkt if parcel_data.coordinates else None
    )
    
    db.add(db_parcel)
    db.commit()
    db.refresh(db_parcel)
    
    # Формирование ответа
    response = ParcelInfo(
        id=db_parcel.id,
        cadastral_number=db_parcel.cadastral_number,
        area=db_parcel.area,
        area_unit=db_parcel.area_unit,
        category=db_parcel.category,
        permitted_use=db_parcel.permitted_use,
        address=db_parcel.address,
        centroid_lat=parcel_data.coordinates.centroid.y if parcel_data.coordinates else None,
        centroid_lon=parcel_data.coordinates.centroid.x if parcel_data.coordinates else None,
        created_at=db_parcel.created_at
    )
    
    # Кэширование результата
    cache.setex(cache_key, 3600, json.dumps(response.dict(), default=str))  # 1 час
    
    return response


@app.get("/parcels/{parcel_id}", response_model=ParcelInfo)
async def get_parcel_info(
    parcel_id: int,
    db: Session = Depends(get_db)
):
    """Получение информации об участке по ID"""
    parcel = db.query(CadastreParcel).filter(CadastreParcel.id == parcel_id).first()
    
    if not parcel:
        raise HTTPException(status_code=404, detail="Участок не найден")
    
    return ParcelInfo(
        id=parcel.id,
        cadastral_number=parcel.cadastral_number,
        area=parcel.area,
        area_unit=parcel.area_unit,
        category=parcel.category,
        permitted_use=parcel.permitted_use,
        address=parcel.address,
        centroid_lat=parcel.coordinates.centroid.y if parcel.coordinates else None,
        centroid_lon=parcel.coordinates.centroid.x if parcel.coordinates else None,
        created_at=parcel.created_at
    )


@app.get("/parcels/{parcel_id}/features", response_model=List[FeatureResponse])
async def get_parcel_features(
    parcel_id: int,
    feature_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получение признаков участка"""
    query = db.query(ParcelFeature).filter(ParcelFeature.parcel_id == parcel_id)
    
    if feature_type:
        query = query.filter(ParcelFeature.feature_type == feature_type)
    
    features = query.all()
    
    if not features:
        raise HTTPException(status_code=404, detail="Признаки не найдены")
    
    return [
        FeatureResponse(
            feature_type=f.feature_type,
            feature_name=f.feature_name,
            feature_value=f.feature_value,
            feature_text=f.feature_text,
            calculation_method=f.calculation_method
        ) for f in features
    ]


@app.post("/evaluate", response_model=LiquidityAssessmentResponse)
async def evaluate_parcel(
    request: ParcelRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    cache: redis.Redis = Depends(get_redis)
):
    """
    Оценка ликвидности участка
    
    Если участок уже оценивался недавно (в течение 24 часов), 
    возвращается кэшированный результат
    """
    # Поиск или создание участка
    if request.cadastral_number:
        parcel = db.query(CadastreParcel).filter(
            CadastreParcel.cadastral_number == request.cadastral_number
        ).first()
    elif request.latitude and request.longitude:
        # Поиск по координатам (упрощенный пример)
        parcel = db.query(CadastreParcel).first()  # Нужна более сложная логика
    else:
        raise HTTPException(status_code=400, detail="Необходимо указать кадастровый номер или координаты")
    
    if not parcel:
        raise HTTPException(status_code=404, detail="Участок не найден")
    
    # Проверка кэша
    cache_key = f"assessment:{parcel.id}"
    cached_result = cache.get(cache_key)
    if cached_result:
        return JSONResponse(content=json.loads(cached_result))
    
    # Проверка последней оценки
    last_assessment = db.query(LiquidityAssessment).filter(
        LiquidityAssessment.parcel_id == parcel.id
    ).order_by(LiquidityAssessment.assessment_date.desc()).first()
    
    if last_assessment and (datetime.now() - last_assessment.assessment_date) < timedelta(hours=24):
        # Возвращаем последнюю оценку
        response = LiquidityAssessmentResponse(
            parcel_id=last_assessment.parcel_id,
            cadastral_number=parcel.cadastral_number,
            liquidity_score=last_assessment.liquidity_score or 0.0,
            liquidity_category=last_assessment.liquidity_category or "unknown",
            predicted_price=last_assessment.predicted_price,
            confidence_interval={
                "lower": last_assessment.confidence_interval_lower,
                "upper": last_assessment.confidence_interval_upper
            } if last_assessment.confidence_interval_lower else None,
            assessment_date=last_assessment.assessment_date,
            explanation=json.loads(last_assessment.features_used) if last_assessment.features_used else {},
            factors=[]  # Можно добавить факторы из отдельной таблицы
        )
        
        # Кэширование
        cache.setex(cache_key, 3600, json.dumps(response.dict(), default=str))
        return response
    
    # Асинхронная оценка
    background_tasks.add_task(perform_assessment, parcel.id, db)
    
    return {
        "message": "Оценка запущена. Результат будет доступен через несколько минут.",
        "parcel_id": parcel.id,
        "status": "processing"
    }


async def perform_assessment(parcel_id: int, db: Session):
    """Асинхронная оценка ликвидности"""
    try:
        # Расчет признаков
        calculator = FeatureCalculator(db)
        feature_result = calculator.calculate_all_features(parcel_id)
        
        if not feature_result.features:
            logger.error(f"Не удалось рассчитать признаки для участка {parcel_id}")
            return
        
        # Сохранение признаков
        calculator.save_features_to_database(parcel_id, feature_result.features)
        
        # Оценка ликвидности
        assessment_service = LiquidityAssessmentService(db)
        assessment_result = assessment_service.assess_parcel(parcel_id)
        
        logger.info(f"Оценка завершена для участка {parcel_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при оценке участка {parcel_id}: {e}")


@app.get("/assessments/{assessment_id}")
async def get_assessment_result(
    assessment_id: int,
    db: Session = Depends(get_db)
):
    """Получение результата оценки по ID"""
    assessment = db.query(LiquidityAssessment).filter(
        LiquidityAssessment.id == assessment_id
    ).first()
    
    if not assessment:
        raise HTTPException(status_code=404, detail="Оценка не найдена")
    
    parcel = db.query(CadastreParcel).filter(
        CadastreParcel.id == assessment.parcel_id
    ).first()
    
    return LiquidityAssessmentResponse(
        parcel_id=assessment.parcel_id,
        cadastral_number=parcel.cadastral_number if parcel else "unknown",
        liquidity_score=assessment.liquidity_score or 0.0,
        liquidity_category=assessment.liquidity_category or "unknown",
        predicted_price=assessment.predicted_price,
        confidence_interval={
            "lower": assessment.confidence_interval_lower,
            "upper": assessment.confidence_interval_upper
        } if assessment.confidence_interval_lower else None,
        assessment_date=assessment.assessment_date,
        explanation=json.loads(assessment.features_used) if assessment.features_used else {},
        factors=[]  # Можно добавить факторы из отдельной таблицы
    )


@app.get("/market/comparables")
async def get_comparable_sales(
    parcel_id: int,
    radius: float = 5.0,  # км
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Получение сопоставимых продаж в радиусе"""
    # Реализация поиска сопоставимых участков
    # Это упрощенный пример
    return {
        "parcel_id": parcel_id,
        "radius_km": radius,
        "comparables": [],
        "average_price": 0,
        "median_price": 0
    }


@app.get("/report/{parcel_id}")
async def generate_report(
    parcel_id: int,
    format: str = "json",
    db: Session = Depends(get_db)
):
    """Генерация отчета об оценке"""
    # Реализация генерации отчета
    # Может возвращать PDF или JSON с детальной информацией
    return {
        "parcel_id": parcel_id,
        "report_type": format,
        "generated_at": datetime.now().isoformat(),
        "data": {
            "basic_info": {},
            "features": {},
            "assessment": {},
            "comparables": {}
        }
    }


@app.get("/analytics/market-trends")
async def get_market_trends(
    region: str,
    period: str = "3m",  # 1m, 3m, 6m, 1y
    db: Session = Depends(get_db)
):
    """Получение рыночных трендов по региону"""
    return {
        "region": region,
        "period": period,
        "trends": {
            "average_price_trend": [],
            "transaction_volume": [],
            "liquidity_index": []
        }
    }


# Обработчики ошибок
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "timestamp": datetime.now().isoformat()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Необработанная ошибка: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "timestamp": datetime.now().isoformat()}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )