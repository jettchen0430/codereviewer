import logging
from logging.handlers import RotatingFileHandler
from ..config.settings import settings

def setup_logger() -> logging.Logger:
    """配置并返回logger实例"""
    logger = logging.getLogger(__name__)
    logger.setLevel(settings.LOG_LEVEL)
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        settings.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(settings.LOG_LEVEL)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(settings.LOG_LEVEL)
    
    # 设置格式
    formatter = logging.Formatter(settings.LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# 创建全局logger实例
logger = setup_logger() 