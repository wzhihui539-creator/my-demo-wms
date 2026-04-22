from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "WMS 仓库管理系统"
    DEBUG: bool = True
    VERSION: str = "1.0.0"
    
    # 数据库 (SQLite 用于演示)
    DATABASE_URL: str = f"sqlite+aiosqlite:///{BASE_DIR / 'wms.db'}"
    
    # Redis (演示环境使用内存)
    REDIS_URL: str = "memory://"
    
    # 安全
    SECRET_KEY: str = "wms-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24小时
    
    # Celery (演示环境使用内存)
    CELERY_BROKER_URL: str = "memory://"
    CELERY_RESULT_BACKEND: str = "memory://"
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
