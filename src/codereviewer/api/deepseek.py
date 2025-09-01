import requests
import json
import logging
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config.settings import settings
import re

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """DeepSeek API 客户端"""
    
    def __init__(self):
        self.base_url = settings.deepseek_url.rstrip('/')
        self.api_key = settings.deepseek_api_key
        self.timeout = settings.api_timeout
        self.max_tokens = 1024
        self.temperature = 0.7
        
        # 根据API端点选择合适的模型
        if "siliconflow" in self.base_url:
            self.model = "Qwen/Qwen3-Coder-480B-A35B-Instruct"  # SiliconFlow支持的模型
        elif "deepseek" in self.base_url:
            self.model = "deepseek-chat"  # 官方DeepSeek模型
        else:
            self.model = "deepseek-chat"  # 默认模型
        
        logger.info(f"DeepSeek client initialized with URL: {self.base_url}, model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(settings.retry_attempts),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _make_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求到DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def analyze_code_diff(self, diff_content: str, context: Optional[str] = None) -> str:
        """分析代码差异并生成审查建议"""
        prompt = self._build_code_review_prompt(diff_content, context)
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的代码审查专家，擅长分析代码差异并提供有价值的改进建议。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        try:
            response = self._make_request(payload)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Failed to analyze code diff: {e}")
            return "代码分析失败，请检查API配置。"
    
    def _build_code_review_prompt(self, diff_content: str, context: Optional[str] = None) -> str:
        """构建代码审查提示"""
        # 为diff添加行号定位
        formatted_diff = self._add_line_numbers_to_diff(diff_content)
        
        base_prompt = f"""
请分析以下代码差异，每行前带有行号和类型（例如 '1: + code' 或 '2: - code'）。
仅关注以 '+' 或 '-' 开头的行。

请从以下几个方面进行分析：
1. 代码质量和可读性
2. 潜在的bug和安全隐患
3. 性能优化建议
4. 代码规范和最佳实践
5. 测试覆盖建议

请提供具体、可操作的改进建议，每条建议应该：
- 明确指出问题所在的行号和类型
- 解释问题的原因和影响
- 提供具体的解决方案或改进建议
- 使用简洁明了的语言

格式要求：
每条建议使用以下格式：
行 X 类型 Y: [具体建议内容]

其中：
- X 是行号
- Y 是行类型（+ 表示新增，- 表示删除）
- 建议内容不超过30个单词

代码差异：
{formatted_diff}
"""
        
        if context:
            base_prompt += f"\n\n额外上下文信息：\n{context}"
        
        return base_prompt
    
    def _add_line_numbers_to_diff(self, diff_str: str) -> str:
        """
        为 Git diff 中的每一行附上其在对应文件中的行号。
        - 对于上下文行和 +行，使用新文件中的行号。
        - 对于 -行，使用旧文件中的行号。
        - 对于 hunk header 行，标记为 "N/A"。
        """
        lines = diff_str.splitlines()
        result_lines = []
        current_old_line = None
        current_new_line = None
        in_hunk = False

        for line in lines:
            hunk_match = re.match(r'@@ -(\d+),\d+ \+(\d+),\d+ @@', line)
            if hunk_match:
                current_old_line = int(hunk_match.group(1))
                current_new_line = int(hunk_match.group(2))
                in_hunk = True
                result_lines.append(f"N/A: {line}")
                continue
            if not in_hunk:
                result_lines.append(f"N/A: {line}")
                continue
            if line.startswith('-'):
                result_lines.append(f"{current_old_line}: {line}")
                current_old_line += 1
            elif line.startswith('+'):
                result_lines.append(f"{current_new_line}: {line}")
                current_new_line += 1
            else:
                result_lines.append(f"{current_new_line}: {line}")
                current_old_line += 1
                current_new_line += 1
        return "\n".join(result_lines)
    
    def generate_review_summary(self, comments: List[Any]) -> str:
        """生成审查摘要"""
        if not comments:
            return "代码审查完成，未发现需要改进的问题。"
        
        # 将Comment对象转换为可序列化的字典
        serializable_comments = []
        for comment in comments:
            if hasattr(comment, '__dict__'):
                # 如果是对象，转换为字典
                comment_dict = {
                    'line': getattr(comment, 'line', 'unknown'),
                    'file_path': getattr(comment, 'file_path', 'unknown'),
                    'comment': getattr(comment, 'comment', 'unknown'),
                    'line_type': str(getattr(comment, 'line_type', 'unknown')),
                    'severity': getattr(comment, 'severity', 'info'),
                    'category': getattr(comment, 'category', 'general')
                }
                serializable_comments.append(comment_dict)
            else:
                # 如果已经是字典，直接使用
                serializable_comments.append(comment)
        
        prompt = f"""
基于以下代码审查评论，生成一个简洁的摘要：

评论列表：
{json.dumps(serializable_comments, ensure_ascii=False, indent=2)}

请生成一个100字以内的摘要，总结主要发现的问题和改进建议。
"""
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个代码审查专家，擅长总结和归纳代码审查结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 200,
            "temperature": 0.5,
            "stream": False
        }
        
        try:
            response = self._make_request(payload)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Failed to generate review summary: {e}")
            return f"代码审查完成，共发现 {len(comments)} 个需要改进的问题。"
    
    def validate_response(self, response: str) -> bool:
        """验证API响应是否有效"""
        return response and len(response.strip()) > 0 and "代码分析失败" not in response 