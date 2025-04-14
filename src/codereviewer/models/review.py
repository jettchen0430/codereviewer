from dataclasses import dataclass
from typing import List, Optional

@dataclass
class CodeComment:
    """代码审查评论模型"""
    line: int
    file_path: str
    comment: str
    line_type: str  # '+' 或 '-'
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "line": self.line,
            "file_path": self.file_path,
            "comment": self.comment,
            "line_type": self.line_type
        }

@dataclass
class MergeRequest:
    """Merge Request信息模型"""
    project_id: int
    mr_iid: int
    head_sha: str
    diff: Optional[List[dict]] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "project_id": self.project_id,
            "mr_iid": self.mr_iid,
            "head_sha": self.head_sha,
            "diff": self.diff
        }

@dataclass
class ReviewResult:
    """代码审查结果模型"""
    mr: MergeRequest
    comments: List[CodeComment]
    success: bool
    error: Optional[str] = None
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "mr": self.mr.to_dict(),
            "comments": [comment.to_dict() for comment in self.comments],
            "success": self.success,
            "error": self.error
        } 