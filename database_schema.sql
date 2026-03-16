-- Схема базы данных для системы оценки ликвидности земельных участков ИЖС
-- PostgreSQL + PostGIS

-- Включение расширения PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- 1. Таблица кадастровых участков
CREATE TABLE cadastre_parcel (
    id SERIAL PRIMARY KEY,
    cadastral_number VARCHAR(100) UNIQUE NOT NULL,
    cadastral_block VARCHAR(50),
    area DECIMAL(15,3), -- площадь в квадратных метрах
    area_unit VARCHAR(20), -- единица измерения площади
    status VARCHAR(50), -- действующий, анулирован и т.д.
    category VARCHAR(100), -- категория земель
    permitted_use VARCHAR(200), -- вид разрешенного использования
    address TEXT,
    coordinates GEOGRAPHY(POLYGON, 4326), -- границы участка в WGS84
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50), -- источник данных
    source_id VARCHAR(100), -- идентификатор в источнике
    
    -- Индексы для производительности
    INDEX idx_cadastral_number (cadastral_number),
    INDEX idx_coordinates USING GIST (coordinates),
    INDEX idx_category (category)
);

-- 2. Таблица признаков участков (рассчитанные метрики)
CREATE TABLE parcel_features (
    id SERIAL PRIMARY KEY,
    parcel_id INTEGER REFERENCES cadastre_parcel(id) ON DELETE CASCADE,
    feature_type VARCHAR(50) NOT NULL, -- тип признака
    feature_name VARCHAR(100) NOT NULL, -- название признака
    feature_value DECIMAL(15,6), -- числовое значение
    feature_text TEXT, -- текстовое значение (если применимо)
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    calculation_method VARCHAR(100), -- метод расчета
    
    UNIQUE(parcel_id, feature_type, feature_name),
    INDEX idx_parcel_features (parcel_id, feature_type)
);

-- 3. Таблица инфраструктурных объектов
CREATE TABLE infrastructure_objects (
    id SERIAL PRIMARY KEY,
    object_type VARCHAR(50) NOT NULL, -- тип объекта (дорога, школа и т.д.)
    object_subtype VARCHAR(100), -- подтип (шоссе, улица и т.д.)
    name VARCHAR(200), -- название
    address TEXT,
    coordinates GEOGRAPHY(POINT, 4326),
    attributes JSONB, -- дополнительные атрибуты в JSON
    source VARCHAR(50),
    source_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_infra_type (object_type),
    INDEX idx_infra_coordinates USING GIST (coordinates),
    INDEX idx_infra_source (source, source_id)
);

-- 4. Таблица расстояний от участков до объектов инфраструктуры
CREATE TABLE parcel_distances (
    id SERIAL PRIMARY KEY,
    parcel_id INTEGER REFERENCES cadastre_parcel(id) ON DELETE CASCADE,
    object_id INTEGER REFERENCES infrastructure_objects(id) ON DELETE CASCADE,
    object_type VARCHAR(50),
    distance_meters DECIMAL(10,2), -- расстояние в метрах
    travel_time_seconds DECIMAL(10,2), -- время в пути в секундах
    travel_method VARCHAR(20), -- способ передвижения (пешком, на авто)
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(parcel_id, object_id, travel_method),
    INDEX idx_parcel_distances (parcel_id, object_type),
    INDEX idx_distance_value (distance_meters)
);

-- 5. Таблица рыночных данных (объявления о продаже)
CREATE TABLE market_listings (
    id SERIAL PRIMARY KEY,
    parcel_id INTEGER REFERENCES cadastre_parcel(id) ON DELETE SET NULL,
    listing_type VARCHAR(20), -- продажа, аренда
    price DECIMAL(15,2), -- цена
    price_per_unit DECIMAL(15,2), -- цена за единицу площади
    price_currency VARCHAR(10), -- валюта
    area DECIMAL(15,3), -- площадь
    area_unit VARCHAR(20),
    listing_date DATE,
    status VARCHAR(30), -- активно, продано, снято
    source VARCHAR(50), -- источник (авито, циан и т.д.)
    source_url TEXT,
    source_id VARCHAR(100),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_market_parcel (parcel_id),
    INDEX idx_market_source (source, source_id),
    INDEX idx_market_price (price),
    INDEX idx_market_date (listing_date)
);

-- 6. Таблица оценок ликвидности
CREATE TABLE liquidity_assessments (
    id SERIAL PRIMARY KEY,
    parcel_id INTEGER REFERENCES cadastre_parcel(id) ON DELETE CASCADE,
    assessment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    liquidity_score DECIMAL(5,4), -- индекс ликвидности 0-1
    liquidity_category VARCHAR(20), -- категория (высокая, средняя, низкая)
    predicted_price DECIMAL(15,2), -- прогнозируемая цена
    confidence_interval_lower DECIMAL(15,2), -- нижняя граница доверительного интервала
    confidence_interval_upper DECIMAL(15,2), -- верхняя граница доверительного интервала
    model_version VARCHAR(50), -- версия модели
    features_used JSONB, -- использованные признаки
    assessment_method VARCHAR(50), -- метод оценки
    
    INDEX idx_assessment_parcel (parcel_id),
    INDEX idx_assessment_date (assessment_date),
    INDEX idx_assessment_score (liquidity_score)
);

-- 7. Таблица факторов, влияющих на оценку (для Explainable AI)
CREATE TABLE assessment_factors (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES liquidity_assessments(id) ON DELETE CASCADE,
    feature_name VARCHAR(100),
    feature_value DECIMAL(15,6),
    feature_importance DECIMAL(10,6), -- вклад признака в оценку
    factor_direction VARCHAR(10), -- positive, negative
    factor_description TEXT, -- текстовое описание влияния
    
    INDEX idx_factor_assessment (assessment_id),
    INDEX idx_factor_importance (feature_importance)
);

-- 8. Таблица спутниковых данных и индексов
CREATE TABLE satellite_data (
    id SERIAL PRIMARY KEY,
    parcel_id INTEGER REFERENCES cadastre_parcel(id) ON DELETE CASCADE,
    date_acquired DATE,
    satellite_source VARCHAR(50), -- Sentinel, Landsat и т.д.
    ndvi DECIMAL(6,4), -- Normalized Difference Vegetation Index
    ndwi DECIMAL(6,4), -- Normalized Difference Water Index
    ndbi DECIMAL(6,4), -- Normalized Difference Built-up Index
    elevation DECIMAL(8,2), -- высота над уровнем моря
    slope DECIMAL(6,4), -- уклон
    aspect DECIMAL(6,4), -- экспозиция склона
    image_url TEXT, -- ссылка на снимок
    
    INDEX idx_satellite_parcel (parcel_id),
    INDEX idx_satellite_date (date_acquired),
    INDEX idx_satellite_ndvi (ndvi)
);

-- 9. Таблица социально-экономических показателей районов
CREATE TABLE socio_economic_data (
    id SERIAL PRIMARY KEY,
    region_code VARCHAR(20), -- код района/муниципалитета
    region_name VARCHAR(200),
    population INTEGER,
    population_density DECIMAL(10,2), -- плотность населения
    average_income DECIMAL(15,2),
    unemployment_rate DECIMAL(6,4),
    crime_rate DECIMAL(8,4),
    education_level DECIMAL(6,4),
    healthcare_access DECIMAL(6,4),
    data_year INTEGER,
    data_source VARCHAR(100),
    
    INDEX idx_socio_region (region_code),
    INDEX idx_socio_year (data_year)
);

-- 10. Таблица пользовательских запросов и кэширования
CREATE TABLE user_requests (
    id SERIAL PRIMARY KEY,
    request_type VARCHAR(50), -- тип запроса
    request_params JSONB, -- параметры запроса
    result_data JSONB, -- результат
    cache_key VARCHAR(200), -- ключ кэша
    response_time_ms INTEGER, -- время ответа в миллисекундах
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(100), -- идентификатор пользователя (если есть)
    
    INDEX idx_request_cache (cache_key),
    INDEX idx_request_type (request_type),
    INDEX idx_request_time (created_at)
);

-- 11. Таблица метаданных о моделях машинного обучения
CREATE TABLE ml_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50), -- CatBoost, LightGBM и т.д.
    training_date TIMESTAMP,
    training_data_size INTEGER,
    accuracy_metrics JSONB, -- метрики качества модели
    feature_importance JSONB, -- важность признаков
    model_path TEXT, -- путь к файлу модели
    is_active BOOLEAN DEFAULT FALSE,
    
    UNIQUE(model_name, model_version),
    INDEX idx_model_active (is_active),
    INDEX idx_model_type (model_type)
);

-- 12. Таблица логов операций
CREATE TABLE operation_logs (
    id SERIAL PRIMARY KEY,
    operation_type VARCHAR(50),
    operation_status VARCHAR(20), -- success, failed, running
    operation_details JSONB,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds DECIMAL(10,3),
    error_message TEXT,
    
    INDEX idx_log_operation (operation_type),
    INDEX idx_log_status (operation_status),
    INDEX idx_log_time (started_at)
);

-- Создание материализованных представлений для ускорения запросов

-- Представление для агрегированных данных по участкам
CREATE MATERIALIZED VIEW parcel_summary AS
SELECT 
    cp.id,
    cp.cadastral_number,
    cp.area,
    cp.coordinates,
    AVG(pf.feature_value) as avg_feature_value,
    COUNT(DISTINCT pd.object_type) as infrastructure_count,
    AVG(pd.distance_meters) as avg_distance,
    COUNT(DISTINCT ml.id) as market_listings_count,
    AVG(ml.price_per_unit) as avg_market_price
FROM cadastre_parcel cp
LEFT JOIN parcel_features pf ON cp.id = pf.parcel_id
LEFT JOIN parcel_distances pd ON cp.id = pd.parcel_id
LEFT JOIN market_listings ml ON cp.id = ml.parcel_id
GROUP BY cp.id, cp.cadastral_number, cp.area, cp.coordinates;

CREATE INDEX idx_parcel_summary_cadastral ON parcel_summary(cadastral_number);
CREATE INDEX idx_parcel_summary_coords ON parcel_summary USING GIST(coordinates);

-- Функция для обновления материализованного представления
CREATE OR REPLACE FUNCTION refresh_parcel_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW parcel_summary;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_cadastre_parcel_updated_at
    BEFORE UPDATE ON cadastre_parcel
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Функции для геометрических расчетов
CREATE OR REPLACE FUNCTION calculate_parcel_shape_factor(polygon GEOGRAPHY)
RETURNS DECIMAL AS $$
DECLARE
    area_val DECIMAL;
    perimeter_val DECIMAL;
BEGIN
    area_val := ST_Area(polygon);
    perimeter_val := ST_Perimeter(polygon);
    
    IF perimeter_val = 0 THEN
        RETURN NULL;
    END IF;
    
    RETURN area_val / (perimeter_val * perimeter_val);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_nearest_infrastructure(
    parcel_point GEOGRAPHY,
    infra_type VARCHAR,
    limit_count INTEGER DEFAULT 5
)
RETURNS TABLE(
    object_id INTEGER,
    object_name VARCHAR,
    distance_meters DECIMAL,
    object_type VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        io.id,
        io.name,
        ST_Distance(parcel_point, io.coordinates)::DECIMAL as distance,
        io.object_type
    FROM infrastructure_objects io
    WHERE io.object_type = infra_type
    ORDER BY distance
    LIMIT limit_count;
END;
$$ LANGUAGE plpgsql;