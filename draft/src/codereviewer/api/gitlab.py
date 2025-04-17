import requests
from typing import Dict, List, Optional
from ..config.settings import settings
from ..utils.logger import logger

class GitLabAPI:
    """GitLab API 客户端"""
    
    def __init__(self):
        self.base_url = settings.GITLAB_URL
        self.headers = {"PRIVATE-TOKEN": settings.GITLAB_TOKEN}
    
    def get_mr_details(self, project_id: int, mr_iid: int) -> Optional[Dict]:
        """获取 Merge Request 的详细信息"""
        url = f"{self.base_url}/projects/{project_id}/merge_requests/{mr_iid}"
        try:
            response = requests.get(url, headers=self.headers, timeout=settings.API_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching MR details: {e}")
            return None
    
    def get_commit_diff(self, project_id: int, sha: str) -> Optional[List[Dict]]:
        """获取提交的 diff 数据"""
        url = f"{self.base_url}/projects/{project_id}/repository/commits/{sha}/diff"
        try:
            response = requests.get(url, headers=self.headers, timeout=settings.API_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching commit diff: {e}")
            return None
    
    def submit_comment(self, project_id: int, sha: str, comment: Dict) -> bool:
        """提交评论到 GitLab"""
        url = f"{self.base_url}/projects/{project_id}/repository/commits/{sha}/comments"
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=comment,
                timeout=settings.API_TIMEOUT
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error(f"Error submitting comment: {e}")
            return False

# 创建全局 GitLab API 客户端实例
gitlab_api = GitLabAPI() 