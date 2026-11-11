"""应用配置"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "校园AI助手平台"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    DATABASE_URL: str = "sqlite:///./campus_ai.db"

    # JWT 安全配置
    SECRET_KEY: str = "campus-ai-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1
    REDIS_PASSWORD: str = "difyai123456"

    CORS_ORIGINS: list = ["*"]

    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    QWEN_API_KEY: str = ""
    QWEN_API_BASE: str = "https://dashscope.aliyuncs.com/api/v1"
    DIFY_API_BASE: str = "http://localhost:8080/api"
    DIFY_API_KEY: str = ""
    DIFY_AGENT_APP_ID: str = ""
    DIFY_WORKFLOW_APP_ID: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
