from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置设置"""
    
    # GitLab 配置
    gitlab_url: str = os.getenv("GITLAB_URL", "")
    gitlab_token: str = os.getenv("GITLAB_TOKEN", "")
    
    # DeepSeek API 配置
    deepseek_url: str = os.getenv("DEEPSEEK_URL", "https://api.deepseek.com")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    
    # Webhook 配置
    webhook_secret: str = os.getenv("WEBHOOK_SECRET", "")
    
    # RAG 配置
    documents_file: str = os.getenv("DOCUMENTS_FILE", "documents.txt")
    embedding_dimension: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    max_retrieved_docs: int = int(os.getenv("MAX_RETRIEVED_DOCS", "3"))
    
    # 应用设置
    max_workers: int = int(os.getenv("MAX_WORKERS", "4"))
    max_comments: int = int(os.getenv("MAX_COMMENTS", "3"))
    api_timeout: int = int(os.getenv("API_TIMEOUT", "30"))
    retry_attempts: int = int(os.getenv("RETRY_ATTEMPTS", "3"))
    retry_delay: int = int(os.getenv("RETRY_DELAY", "1"))
    
    # 日志配置
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "reviewer.log")
    
    class Config:
        env_file = ".env"


# 全局设置实例
settings = Settings() 