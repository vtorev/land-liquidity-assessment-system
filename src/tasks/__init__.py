# Модуль для фоновых задач Celery
# Импортируем Celery приложение для доступа из других модулей

from .celery_app import celery_app

# Импортируем задачи для регистрации в Celery
from .data_tasks import (
    update_market_data,
    update_infrastructure_data,
    update_cadastre_data,
    cleanup_old_data,
    download_osm_data,
    process_satellite_imagery
)

from .ml_tasks import (
    retrain_models,
    assess_parcel_liquidity,
    batch_assess_parcels,
    calculate_feature_importance,
    generate_model_report,
    validate_model_performance,
    create_synthetic_data
)

from .feature_tasks import (
    calculate_parcel_features,
    calculate_batch_features,
    calculate_geospatial_features,
    calculate_infrastructure_distances,
    update_feature_cache,
    validate_features,
    cleanup_old_features,
    generate_feature_statistics
)

__all__ = [
    'celery_app',
    # Data tasks
    'update_market_data',
    'update_infrastructure_data', 
    'update_cadastre_data',
    'cleanup_old_data',
    'download_osm_data',
    'process_satellite_imagery',
    # ML tasks
    'retrain_models',
    'assess_parcel_liquidity',
    'batch_assess_parcels',
    'calculate_feature_importance',
    'generate_model_report',
    'validate_model_performance',
    'create_synthetic_data',
    # Feature tasks
    'calculate_parcel_features',
    'calculate_batch_features',
    'calculate_geospatial_features',
    'calculate_infrastructure_distances',
    'update_feature_cache',
    'validate_features',
    'cleanup_old_features',
    'generate_feature_statistics'
]