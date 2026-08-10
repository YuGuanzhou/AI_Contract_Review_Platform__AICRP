"""
应用配置模块
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用配置
    APP_NAME: str = "中小企业智能合同审查平台"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置（真实密码通过 .env 的 DATABASE_URL 注入，禁止硬编码）
    DATABASE_URL: str = "mysql+aiomysql://root:your-database-password@localhost:3306/contract_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Redis配置
    REDIS_URL: str = "redis://:12345678@localhost:6379/0"
    REDIS_POOL_SIZE: int = 10
    
    # MinIO配置
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "contracts"
    
    # JWT配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # AI配置
    AI_PROVIDER: str = "deepseek"  # deepseek, openai, local
    # 密钥通过 .env / 环境变量注入，禁止硬编码到代码中（见项目根目录 .env 与 .env.example）
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = ["pdf", "doc", "docx", "txt"]
    STORAGE_TYPE: str = "minio"  # local, minio
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
    ]
    
    # 安全配置
    SECURITY_PASSWORD_SALT: str = "your-password-salt-change-in-production"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/app.log"
    
    # 任务队列配置
    CELERY_BROKER_URL: str = "redis://:12345678@localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://:12345678@localhost:6379/2"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()