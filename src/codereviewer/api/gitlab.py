import requests
from typing import List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
from ..config.settings import settings
from ..models.review import MergeRequest, Commit, FileDiff

logger = logging.getLogger(__name__)


class GitLabClient:
    """GitLab API 客户端"""
    
    def _normalize_gitlab_url(self, url: str) -> str:
        """标准化GitLab URL，确保格式正确"""
        if not url:
            return ""
        
        # 移除末尾的斜杠
        url = url.rstrip('/')
        
        # 如果URL包含项目路径，只保留域名部分
        if '/api/' in url:
            url = url.split('/api/')[0]
        elif '/projects/' in url:
            url = url.split('/projects/')[0]
        elif '/groups/' in url:
            url = url.split('/groups/')[0]
        
        # 确保URL以http://或https://开头
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        logger.info(f"Normalized GitLab URL: {url}")
        return url
    
    def __init__(self):
        # 确保GitLab URL格式正确
        self.base_url = self._normalize_gitlab_url(settings.gitlab_url)
        self.token = settings.gitlab_token
        self.headers = {
            "PRIVATE-TOKEN": self.token,
            "Content-Type": "application/json"
        }
        self.timeout = settings.api_timeout
        
        # 验证配置
        if not self.base_url:
            logger.error("GITLAB_URL is not configured")
            raise ValueError("GITLAB_URL is not configured")
        if not self.token:
            logger.error("GITLAB_TOKEN is not configured")
            raise ValueError("GITLAB_TOKEN is not configured")
        
        logger.info(f"GitLab client initialized with URL: {self.base_url}")
    
    @retry(
        stop=stop_after_attempt(settings.retry_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """发送HTTP请求到GitLab API"""
        url = f"{self.base_url}/api/v4{endpoint}"
        kwargs.setdefault('headers', self.headers)
        kwargs.setdefault('timeout', self.timeout)
        
        logger.debug(f"Making {method} request to: {url}")
        
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {method} {url} - Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def get_merge_request(self, project_id: int, mr_iid: int) -> Optional[MergeRequest]:
        """获取合并请求详情"""
        try:
            endpoint = f"/projects/{project_id}/merge_requests/{mr_iid}"
            response = self._make_request("GET", endpoint)
            data = response.json()
            
            return MergeRequest(
                id=data['id'],
                iid=data['iid'],
                project_id=project_id,
                title=data['title'],
                description=data.get('description'),
                source_branch=data['source_branch'],
                target_branch=data['target_branch'],
                state=data['state'],
                created_at=str(data['created_at']),
                updated_at=str(data['updated_at']),
                head_sha=data.get('sha', data.get('head_sha')),
                base_sha=data.get('base_sha')
            )
        except Exception as e:
            logger.error(f"Failed to fetch merge request {mr_iid}: {e}")
            return None
    
    def get_commit(self, project_id: int, sha: str) -> Optional[Commit]:
        """获取提交详情"""
        try:
            endpoint = f"/projects/{project_id}/repository/commits/{sha}"
            response = self._make_request("GET", endpoint)
            data = response.json()
            
            return Commit(
                sha=data['id'],
                message=data['message'],
                author_name=data['author_name'],
                author_email=data['author_email'],
                created_at=str(data['created_at'])
            )
        except Exception as e:
            logger.error(f"Failed to fetch commit {sha}: {e}")
            return None
    
    def get_commit_diff(self, project_id: int, sha: str) -> List[FileDiff]:
        """获取提交的差异"""
        try:
            endpoint = f"/projects/{project_id}/repository/commits/{sha}/diff"
            response = self._make_request("GET", endpoint)
            diffs_data = response.json()
            
            diffs = []
            for diff_data in diffs_data:
                diff = FileDiff(
                    old_path=diff_data.get('old_path'),
                    new_path=diff_data['new_path'],
                    diff=diff_data['diff']
                )
                diffs.append(diff)
            
            return diffs
        except Exception as e:
            logger.error(f"Failed to fetch commit diff for {sha}: {e}")
            return []
    
    def get_branch_commits(self, project_id: int, branch: str, limit: int = 10) -> List[Commit]:
        """获取分支的提交列表"""
        try:
            endpoint = f"/projects/{project_id}/repository/commits?ref_name={branch}&per_page={limit}"
            response = self._make_request("GET", endpoint)
            commits_data = response.json()
            
            commits = []
            for commit_data in commits_data:
                commit = Commit(
                    sha=commit_data['id'],
                    message=commit_data['message'],
                    author_name=commit_data['author_name'],
                    author_email=commit_data['author_email'],
                    created_at=str(commit_data['created_at'])
                )
                commits.append(commit)
            
            return commits
        except Exception as e:
            logger.error(f"Failed to fetch commits for branch {branch}: {e}")
            return []
    
    def post_comment(self, project_id: int, sha: str, comment: Dict[str, Any]) -> bool:
        """在提交上发布评论"""
        try:
            endpoint = f"/projects/{project_id}/repository/commits/{sha}/comments"
            response = self._make_request("POST", endpoint, json=comment)
            return response.status_code == 201
        except Exception as e:
            logger.error(f"Failed to post comment: {e}")
            return False
    
    def get_project_info(self, project_id: int) -> Optional[Dict[str, Any]]:
        """获取项目信息"""
        try:
            endpoint = f"/projects/{project_id}"
            response = self._make_request("GET", endpoint)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch project info: {e}")
            return None
    
    def validate_webhook(self, data: Dict[str, Any], signature: str) -> bool:
        """验证webhook签名"""
        # 这里应该实现webhook签名验证逻辑
        # 为了简化，暂时返回True
        return True 