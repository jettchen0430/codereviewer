import os
from typing import Dict, Any

class Settings:
    """应用配置类"""
    
    # GitLab配置
    GITLAB_URL: str = os.getenv("GITLAB_URL", "")
    GITLAB_TOKEN: str = os.getenv("GITLAB_TOKEN", "")
    
    # DeepSeek配置
    DEEPSEEK_URL: str = os.getenv("DEEPSEEK_URL", "")
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    
    # Webhook配置
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "")
    
    # RAG配置
    DOCUMENTS_FILE: str = "documents.txt"
    EMBEDDING_DIMENSION: int = 384
    MAX_RETRIEVED_DOCS: int = 2
    
    # 应用配置
    MAX_WORKERS: int = 5
    MAX_COMMENTS: int = 3
    API_TIMEOUT: int = 30
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: int = 2
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "reviewer.log"
    
    @classmethod
    def validate(cls) -> None:
        """验证必要的配置项"""
        required_vars = {
            "GITLAB_URL": cls.GITLAB_URL,
            "GITLAB_TOKEN": cls.GITLAB_TOKEN,
            "DEEPSEEK_URL": cls.DEEPSEEK_URL,
            "DEEPSEEK_API_KEY": cls.DEEPSEEK_API_KEY,
            "WEBHOOK_SECRET": cls.WEBHOOK_SECRET
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """将配置转换为字典"""
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }

# 创建全局配置实例
settings = Settings() 