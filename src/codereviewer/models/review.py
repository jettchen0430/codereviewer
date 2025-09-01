from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LineType(str, Enum):
    """行类型枚举"""
    ADDED = "+"
    DELETED = "-"
    CONTEXT = " "


class Comment(BaseModel):
    """代码审查评论模型"""
    line: int = Field(..., description="评论所在行号")
    file_path: str = Field(..., description="文件路径")
    comment: str = Field(..., description="评论内容")
    line_type: LineType = Field(..., description="行类型")
    severity: str = Field(default="info", description="评论严重程度")
    category: str = Field(default="general", description="评论类别")


class DiffHunk(BaseModel):
    """Diff 块模型"""
    old_start: int = Field(..., description="旧文件起始行号")
    old_lines: int = Field(..., description="旧文件行数")
    new_start: int = Field(..., description="新文件起始行号")
    new_lines: int = Field(..., description="新文件行数")
    content: str = Field(..., description="Diff 内容")


class FileDiff(BaseModel):
    """文件差异模型"""
    old_path: Optional[str] = Field(None, description="旧文件路径")
    new_path: str = Field(..., description="新文件路径")
    diff: str = Field(..., description="差异内容")
    hunks: List[DiffHunk] = Field(default_factory=list, description="Diff 块列表")


class MergeRequest(BaseModel):
    """合并请求模型"""
    id: int = Field(..., description="MR ID")
    iid: int = Field(..., description="MR IID")
    project_id: int = Field(..., description="项目 ID")
    title: str = Field(..., description="MR 标题")
    description: Optional[str] = Field(None, description="MR 描述")
    source_branch: str = Field(..., description="源分支")
    target_branch: str = Field(..., description="目标分支")
    state: str = Field(..., description="MR 状态")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    head_sha: Optional[str] = Field(None, description="源分支的最新提交SHA")
    base_sha: Optional[str] = Field(None, description="目标分支的基准提交SHA")


class Commit(BaseModel):
    """提交模型"""
    sha: str = Field(..., description="提交 SHA")
    message: str = Field(..., description="提交消息")
    author_name: str = Field(..., description="作者姓名")
    author_email: str = Field(..., description="作者邮箱")
    created_at: str = Field(..., description="创建时间")


class ReviewRequest(BaseModel):
    """审查请求模型"""
    merge_request: MergeRequest = Field(..., description="合并请求信息")
    commit: Commit = Field(..., description="提交信息")
    diffs: List[FileDiff] = Field(default_factory=list, description="文件差异列表")
    context: Dict[str, Any] = Field(default_factory=dict, description="额外上下文信息")


class ReviewResult(BaseModel):
    """审查结果模型"""
    request_id: str = Field(..., description="请求 ID")
    merge_request_id: int = Field(..., description="MR ID")
    comments: List[Comment] = Field(default_factory=list, description="生成的评论")
    summary: str = Field(..., description="审查摘要")
    status: str = Field(default="completed", description="审查状态")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")


class ReviewContext(BaseModel):
    """审查上下文模型"""
    project_guidelines: List[str] = Field(default_factory=list, description="项目指导原则")
    code_standards: List[str] = Field(default_factory=list, description="代码标准")
    best_practices: List[str] = Field(default_factory=list, description="最佳实践")
    common_issues: List[str] = Field(default_factory=list, description="常见问题") 