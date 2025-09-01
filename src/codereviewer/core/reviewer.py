import re
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from ..models.review import (
    ReviewRequest, ReviewResult, Comment, LineType, 
    ReviewContext, FileDiff
)
from ..api.gitlab import GitLabClient
from ..api.deepseek import DeepSeekClient
from ..utils.rag_utils import rag_engine
from ..config.settings import settings

logger = logging.getLogger(__name__)


class CodeReviewer:
    """代码审查器，使用LangGraph构建审查工作流"""
    
    def __init__(self):
        self.gitlab_client = GitLabClient()
        self.deepseek_client = DeepSeekClient()
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """构建审查工作流图"""
        
        # 定义状态图 - 使用字典作为状态
        workflow = StateGraph(dict)
        
        # 添加节点
        workflow.add_node("extract_context", self._extract_context)
        workflow.add_node("analyze_diffs", self._analyze_diffs)
        workflow.add_node("generate_comments", self._generate_comments)
        workflow.add_node("post_comments", self._post_comments)
        workflow.add_node("generate_summary", self._generate_summary)
        
        # 定义工作流
        workflow.set_entry_point("extract_context")
        workflow.add_edge("extract_context", "analyze_diffs")
        workflow.add_edge("analyze_diffs", "generate_comments")
        workflow.add_edge("generate_comments", "post_comments")
        workflow.add_edge("post_comments", "generate_summary")
        workflow.add_edge("generate_summary", END)
        
        return workflow.compile()
    
    def _extract_context(self, state: dict) -> dict:
        """提取审查上下文"""
        try:
            mr = state["merge_request"]
            diff = state["diffs"][0].diff
            logger.info(f"Extracting context for MR {mr.iid}")
            
            # 获取项目信息
            project_info = self.gitlab_client.get_project_info(mr.project_id)
            if project_info:
                state["project_info"] = project_info
            
            # 获取知识库上下文
            query = f"code review for {diff}"
            knowledge_context = rag_engine.get_knowledge_context(query)
            if knowledge_context:
                state["knowledge_context"] = knowledge_context
            
            logger.info("Context extraction completed")
            return state
        except Exception as e:
            logger.error(f"Failed to extract context: {e}")
            return state
    
    def _analyze_diffs(self, state: dict) -> dict:
        """分析代码差异"""
        try:
            mr = state["merge_request"]
            logger.info(f"Analyzing diffs for MR {mr.iid}")
            
            # 解析diff内容，提取行号信息
            for diff in state["diffs"]:
                diff.hunks = self._parse_diff_hunks(diff.diff)
            
            logger.info(f"Analyzed {len(state['diffs'])} file diffs")
            return state
        except Exception as e:
            logger.error(f"Failed to analyze diffs: {e}")
            return state
    
    def _parse_diff_hunks(self, diff_content: str) -> List[Dict[str, Any]]:
        """解析diff内容，提取hunk信息"""
        hunks = []
        lines = diff_content.splitlines()
        
        for line in lines:
            # 匹配hunk header: @@ -old_start,old_lines +new_start,new_lines @@
            match = re.match(r'^@@ -(\d+),(\d+) \+(\d+),(\d+) @@', line)
            if match:
                hunk = {
                    "old_start": int(match.group(1)),
                    "old_lines": int(match.group(2)),
                    "new_start": int(match.group(3)),
                    "new_lines": int(match.group(4)),
                    "content": line
                }
                hunks.append(hunk)
        
        return hunks
    
    def _generate_comments(self, state: dict) -> dict:
        """生成代码审查评论"""
        try:
            mr = state["merge_request"]
            logger.info(f"Generating comments for MR {mr.iid}")
            
            all_comments = []
            
            for diff in state["diffs"]:
                if not diff.diff.strip():
                    continue
                
                # 获取知识上下文
                context = state.get("knowledge_context", "")
                
                # 分析代码差异
                analysis = self.deepseek_client.analyze_code_diff(diff.diff, context)
                
                # 解析评论
                comments = self._parse_comments(analysis, diff.new_path)
                if comments:
                    all_comments.extend(comments)
                    logger.info(f"Generated {len(comments)} comments for {diff.new_path}")
                else:
                    logger.warning(f"No comments generated for {diff.new_path}")
            
            # 限制评论数量
            max_comments = settings.max_comments
            if len(all_comments) > max_comments:
                logger.info(f"Limiting comments from {len(all_comments)} to {max_comments}")
                all_comments = all_comments[:max_comments]
            
            # 将评论添加到状态中
            state["generated_comments"] = all_comments
            
            logger.info(f"Generated {len(all_comments)} comments total")
            return state
        except Exception as e:
            logger.error(f"Failed to generate comments: {e}")
            return state
    
    def _parse_comments(self, analysis: str, file_path: str) -> List[Comment]:
        """解析LLM生成的评论"""
        comments = []
        lines = analysis.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 匹配中文格式 "行 X 类型 Y: comment" 和英文格式 "Line X Type Y: comment"
            match = re.search(r'(?:行|Line)\s*(\d+)\s*(?:类型|Type)\s*([+-])\s*:\s*(.*)', line, re.IGNORECASE)
            if match:
                line_num = int(match.group(1))
                line_type = LineType(match.group(2))
                comment_text = match.group(3).strip()
                
                comment = Comment(
                    line=line_num,
                    file_path=file_path,
                    comment=comment_text,
                    line_type=line_type
                )
                comments.append(comment)
            else:
                # 如果没有匹配到标准格式，尝试其他可能的格式
                logger.debug(f"Failed to parse comment line: {line}")
        
        return comments
    
    def _post_comments(self, state: dict) -> dict:
        """发布评论到GitLab"""
        try:
            mr = state["merge_request"]
            logger.info(f"Posting comments for MR {mr.iid}")
            
            comments = state.get("generated_comments", [])
            if not comments:
                logger.info("No comments to post")
                return state
            
            # 获取提交SHA
            commit_sha = state["commit"].sha
            
            # 发布评论
            posted_count = 0
            for comment in comments:
                # 映射行类型为GitLab API格式
                if comment.line_type == LineType.ADDED:
                    line_type = "new"
                elif comment.line_type == LineType.DELETED:
                    line_type = "old"
                else:
                    line_type = "new"
                
                comment_data = {
                    "note": comment.comment,
                    "path": comment.file_path,
                    "line": comment.line,
                    "line_type": line_type
                }
                
                success = self.gitlab_client.post_comment(
                    mr.project_id,
                    commit_sha,
                    comment_data
                )
                
                if success:
                    posted_count += 1
                    logger.info(f"Posted comment on line {comment.line} of {comment.file_path}")
                else:
                    logger.warning(f"Failed to post comment on line {comment.line}")
            
            state["posted_comments_count"] = posted_count
            logger.info(f"Posted {posted_count}/{len(comments)} comments")
            return state
        except Exception as e:
            logger.error(f"Failed to post comments: {e}")
            return state
    
    def _generate_summary(self, state: dict) -> dict:
        """生成审查摘要"""
        try:
            mr = state["merge_request"]
            logger.info(f"Generating summary for MR {mr.iid}")
            
            comments = state.get("generated_comments", [])
            summary = self.deepseek_client.generate_review_summary(comments)
            
            state["review_summary"] = summary
            logger.info("Summary generation completed")
            return state
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return state
    
    def review(self, project_id: int, mr_iid: int) -> ReviewResult:
        """执行代码审查"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting code review for MR {mr_iid} in project {project_id}")
            
            # 获取MR详情
            mr = self.gitlab_client.get_merge_request(project_id, mr_iid)
            if not mr:
                raise ValueError(f"Failed to fetch merge request {mr_iid}")
            
            # 检查head_sha是否存在
            if not mr.head_sha:
                logger.warning(f"MR {mr_iid} has no head_sha, trying to get latest commit from source branch")
                # 如果没有head_sha，尝试从源分支获取最新提交
                try:
                    # 获取源分支的最新提交
                    branch_commits = self.gitlab_client.get_branch_commits(project_id, mr.source_branch, limit=1)
                    if branch_commits:
                        commit = branch_commits[0]
                        logger.info(f"Using latest commit from source branch: {commit.sha}")
                    else:
                        raise ValueError(f"Could not find commits in source branch {mr.source_branch}")
                except Exception as e:
                    logger.error(f"Failed to get latest commit from source branch: {e}")
                    raise ValueError(f"MR {mr_iid} has no head_sha and could not determine latest commit")
            else:
                # 获取提交信息
                commit = self.gitlab_client.get_commit(project_id, mr.head_sha)
                if not commit:
                    raise ValueError(f"Failed to fetch commit {mr.head_sha}")
            
            # 获取差异
            diffs = self.gitlab_client.get_commit_diff(project_id, commit.sha)
            
            # 创建审查请求
            request = ReviewRequest(
                merge_request=mr,
                commit=commit,
                diffs=diffs,
                context={}
            )
            
            # 将ReviewRequest转换为字典传递给工作流
            workflow_state = {
                "merge_request": mr,
                "commit": commit,
                "diffs": diffs,
                "context": {}
            }
            
            # 执行工作流
            final_state = self.workflow.invoke(workflow_state)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 构建审查结果
            result = ReviewResult(
                request_id=f"review_{mr_iid}_{int(start_time)}",
                merge_request_id=mr_iid,
                comments=final_state.get("generated_comments", []),
                summary=final_state.get("review_summary", "审查完成"),
                status="completed",
                processing_time=processing_time
            )
            
            logger.info(f"Code review completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Code review failed: {e}")
            processing_time = time.time() - start_time
            
            return ReviewResult(
                request_id=f"review_{mr_iid}_{int(start_time)}",
                merge_request_id=mr_iid,
                comments=[],
                summary=f"审查失败: {str(e)}",
                status="failed",
                processing_time=processing_time
            )


# 全局代码审查器实例
code_reviewer = CodeReviewer() 