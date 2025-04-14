import requests
from typing import Dict, Optional
from tenacity import retry, stop_after_attempt, wait_fixed
from ..config.settings import settings
from ..utils.logger import logger

class DeepSeekAPI:
    """DeepSeek API 客户端"""
    
    def __init__(self):
        self.base_url = settings.DEEPSEEK_URL
        self.headers = {
            "Authorization": settings.DEEPSEEK_API_KEY,
            "Content-Type": "application/json"
        }
    
    @retry(stop=stop_after_attempt(settings.RETRY_ATTEMPTS), 
           wait=wait_fixed(settings.RETRY_DELAY))
    def analyze_code(self, prompt: str) -> Optional[str]:
        """调用 DeepSeek API 分析代码"""
        payload = {
            "model": "deepseek-ai/DeepSeek-V3",
            "stream": False,
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            "stop": [],
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=self.headers,
                timeout=settings.API_TIMEOUT
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except requests.RequestException as e:
            logger.error(f"Error calling DeepSeek API: {e}")
            return None

# 创建全局 DeepSeek API 客户端实例
deepseek_api = DeepSeekAPI() 