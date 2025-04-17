from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor
from ..models.review import CodeComment, MergeRequest, ReviewResult
from ..api.gitlab import gitlab_api
from ..api.deepseek import deepseek_api
from ..utils.diff_utils import format_diff_for_analysis, parse_comment
from ..utils.rag_utils import rag_utils
from ..config.settings import settings
from ..utils.logger import logger

class CodeReviewer:
    """代码审查核心类"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
        self.diff_cache = {}
    
    def review_merge_request(self, project_id: int, mr_iid: int) -> ReviewResult:
        """审查 Merge Request"""
        # 获取 MR 详情
        mr_details = gitlab_api.get_mr_details(project_id, mr_iid)
        if not mr_details:
            return ReviewResult(
                mr=MergeRequest(project_id, mr_iid, ""),
                comments=[],
                success=False,
                error="Failed to fetch MR details"
            )
        
        head_sha = mr_details.get('diff_refs', {}).get('head_sha')
        if not head_sha:
            return ReviewResult(
                mr=MergeRequest(project_id, mr_iid, ""),
                comments=[],
                success=False,
                error="Failed to get head_sha"
            )
        
        # 获取 diff
        commit_diff = gitlab_api.get_commit_diff(project_id, head_sha)
        if not commit_diff:
            return ReviewResult(
                mr=MergeRequest(project_id, mr_iid, head_sha),
                comments=[],
                success=False,
                error="Failed to fetch commit diff"
            )
        
        # 缓存 diff
        for diff in commit_diff:
            diff_content = diff.get('diff', '')
            self.diff_cache[(project_id, head_sha, diff.get('new_path', ''))] = diff_content
        
        # 分析代码
        comments = self._analyze_code(commit_diff)
        if not comments:
            logger.warning("No comments generated, retrying with cached diff")
            comments = self._retry_analyze_code(project_id, head_sha)
        
        # 限制评论数量
        comments = comments[:settings.MAX_COMMENTS]
        
        # 提交评论
        success = self._submit_comments(project_id, head_sha, comments)
        
        return ReviewResult(
            mr=MergeRequest(project_id, mr_iid, head_sha, commit_diff),
            comments=comments,
            success=success
        )
    
    def _analyze_code(self, commit_diff: List[Dict]) -> List[CodeComment]:
        """分析代码并生成评论"""
        comments = []
        formatted_diff = format_diff_for_analysis(commit_diff)
        
        # 使用RAG检索相关文档
        retrieved_docs = rag_utils.search(formatted_diff, k=settings.MAX_RETRIEVED_DOCS)
        context = "\n".join([doc.document.content for doc in retrieved_docs])
        
        prompt = f"""
        分析以下代码 diff，每行前带有行号和类型（例如 '1: + code' 或 '2: - code'）。  
        仅关注以 '+' 或 '-' 开头的行。  
        请用中文提供最多 3 条有意义的建议，每条严格按照以下格式：  
        "行 X 类型 Y: 建议（30 字以内）, 原始代码"，其中 'X' 是行号，'Y' 是 '+' 或 '-'。

        此外，请参考以下相关文档以增强分析：  
        {context}

        {formatted_diff}
        """
        
        try:
            llm_response = deepseek_api.analyze_code(prompt)
            if not llm_response:
                return []
                
            for comment in llm_response.split('\n'):
                parsed = parse_comment(comment)
                if parsed:
                    comments.append(CodeComment(
                        line=parsed["line"],
                        file_path="",  # 需要从diff中获取
                        comment=parsed["comment"],
                        line_type=parsed["line_type"]
                    ))
        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
        
        return comments
    
    def _retry_analyze_code(self, project_id: int, sha: str) -> List[CodeComment]:
        """使用缓存的 diff 重新分析代码"""
        comments = []
        for key in self.diff_cache:
            if key[0] == project_id and key[1] == sha:
                diff_content = self.diff_cache[key]
                formatted_diff = format_diff_for_analysis([{"diff": diff_content}])
                
                # 使用RAG检索相关文档
                retrieved_docs = rag_utils.search(formatted_diff, k=settings.MAX_RETRIEVED_DOCS)
                context = "\n".join([doc.document.content for doc in retrieved_docs])
                
                prompt = f"""
                分析以下代码 diff，每行前带有行号和类型（例如 '1: + code' 或 '2: - code'）。  
                仅关注以 '+' 或 '-' 开头的行。  
                请用中文提供最多 3 条有意义的建议，每条严格按照以下格式：  
                "行 X 类型 Y: 建议（30 字以内）, 原始代码"，其中 'X' 是行号，'Y' 是 '+' 或 '-'。

                此外，请参考以下相关文档以增强分析：  
                {context}

                {formatted_diff}
                """
                
                try:
                    llm_response = deepseek_api.analyze_code(prompt)
                    if llm_response:
                        for comment in llm_response.split('\n'):
                            parsed = parse_comment(comment)
                            if parsed:
                                comments.append(CodeComment(
                                    line=parsed["line"],
                                    file_path=key[2],
                                    comment=parsed["comment"],
                                    line_type=parsed["line_type"]
                                ))
                except Exception as e:
                    logger.error(f"Retry analysis failed: {e}")
        
        return comments
    
    def _submit_comments(self, project_id: int, sha: str, comments: List[CodeComment]) -> bool:
        """提交评论到 GitLab"""
        success = True
        for comment in comments:
            comment_data = {
                "line": comment.line,
                "path": comment.file_path,
                "note": comment.comment
            }
            if not gitlab_api.submit_comment(project_id, sha, comment_data):
                success = False
        return success

# 创建全局代码审查实例
reviewer = CodeReviewer() 