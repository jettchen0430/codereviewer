from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import requests
import json
import re
import os
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
import numpy as np

app = Flask(__name__)

# ### 环境变量验证
GITLAB_URL = os.getenv("GITLAB_URL")
if not GITLAB_URL:
    raise ValueError("GITLAB_URL is required")

GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
if not GITLAB_TOKEN:
    raise ValueError("GITLAB_TOKEN is required")

DEEPSEEK_URL = os.getenv("DEEPSEEK_URL")
if not DEEPSEEK_URL:
    raise ValueError("DEEPSEEK_URL is required")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY is required")

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
if not WEBHOOK_SECRET:
    raise ValueError("WEBHOOK_SECRET is required")

# Added LightRAG server URL validation
LIGHTRAG_SERVER_URL = os.getenv("LIGHTRAG_SERVER_URL")
if not LIGHTRAG_SERVER_URL:
    raise ValueError("LIGHTRAG_SERVER_URL is required")

# ### 日志配置
# logging.basicConfig(level=logging.INFO, filename="reviewer.log", format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('reviewer.log', encoding='utf-8')
file_handler.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ### 定义线程池
executor = ThreadPoolExecutor(max_workers=5)

# ### Webhook 路由
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """处理 GitLab Webhook 请求，异步触发代码审查"""
    if request.headers.get('X-Gitlab-Token') != WEBHOOK_SECRET:
        return jsonify({"error": "Invalid request source"}), 403
    data = request.json
    if not data or 'event_type' not in data:
        return jsonify({"error": "Invalid request data"}), 400
    if data.get('event_type') == 'merge_request':
        mr_iid = data['object_attributes']['iid']
        project_id = data['project']['id']
        executor.submit(trigger_review, project_id, mr_iid)
    return jsonify({"status": "success"}), 200

# ### 触发代码审查
def trigger_review(project_id, mr_iid):
    """触发代码审查并提交评论"""
    mr_details = get_mr_details(project_id, mr_iid)
    if not mr_details:
        logger.error("Failed to fetch MR details")
        return
    head_sha = mr_details.get('diff_refs', {}).get('head_sha')
    if not head_sha:
        logger.error("Failed to get head_sha")
        return
    
    commit_diff = get_commit_diff(project_id, head_sha)
    if not commit_diff:
        logger.error("Failed to fetch commit diff")
        return
    
    comments = analyze_code_with_llm(commit_diff)
    comments = comments[:3]  # 限制评论数量不超过 3 个
    submit_comments_to_commit(project_id, head_sha, comments)
    logger.info(f"Reviewed commit {head_sha} in project {project_id}, submitted {len(comments)} comments")

# ### 获取 Merge Request 详情
def get_mr_details(project_id, mr_iid):
    """获取 Merge Request 的详细信息"""
    url = f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching MR details: {e}")
        return None

# ### 获取提交的 diff 数据
def get_commit_diff(project_id, sha):
    """获取提交的 diff 数据"""
    url = f"{GITLAB_URL}/projects/{project_id}/repository/commits/{sha}/diff"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching commit diff: {e}")
        return None

# ### 为 diff 添加行号
def add_new_file_line_numbers(diff_str: str) -> str:
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

# ### 调用 DeepSeek API
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def call_deepseek_api(prompt: str) -> str:
    """调用 DeepSeek API 并返回响应内容，支持重试"""
    payload = {
        "model": "deepseek-ai/DeepSeek-V3", # Consider making model configurable
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
    headers = {"Authorization": DEEPSEEK_API_KEY, "Content-Type": "application/json"}
    response = requests.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=90)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

# ### 使用 LLM 分析代码 (调用 LightRAG API 获取上下文)
def analyze_code_with_llm(commit_diff):
    """使用 DeepSeek 模型分析代码 diff，并利用 LightRAG API 获取上下文，生成评论"""
    comments = []
    for diff in commit_diff:
        new_file_path = diff.get('new_path', '')
        diff_content = diff.get('diff', '')
        formatted_diff = add_new_file_line_numbers(diff_content)
        
        # Call LightRAG API to get context
        context = ""
        try:
            lightrag_query_url = f"{LIGHTRAG_SERVER_URL.rstrip('/')}/query"
            # Using /context endpoint to get only the context string
            # lightrag_query_url = f"{LIGHTRAG_SERVER_URL.rstrip('/')}/query/context" 
            payload = {"query": diff_content, "mode": "mix"} # Consider making mode configurable
            headers = {"Content-Type": "application/json"}
            # Add API key header if LIGHTRAG_API_KEY is set
            lightrag_api_key = os.getenv("LIGHTRAG_API_KEY")
            if lightrag_api_key:
                headers["Authorization"] = f"Bearer {lightrag_api_key}" # Assuming Bearer token auth based on README

            response = requests.post(lightrag_query_url, json=payload, headers=headers, timeout=120)
            response.raise_for_status()
            
            # --- Adjust context extraction based on actual LightRAG API response ---
            # Example 1: Assuming response JSON has a 'context' key with the context string
            # context = response.json().get("context", "") 
            
            # Example 2: Assuming response JSON has 'answer' key containing context
            # context = response.json().get("answer", "") 
            
            # Example 3: If using /query, the context might be part of the 'answer' 
            # For now, let's assume the main 'answer' contains the relevant context.
            # This might need refinement based on how LightRAG structures its response.
            context = response.json().get("response", "No context retrieved from LightRAG.")
            logger.info(f"Retrieved context from LightRAG for {new_file_path}")

        except requests.RequestException as e:
            logger.error(f"Failed to query LightRAG API: {e}")
            context = "Failed to retrieve context from LightRAG."
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LightRAG response: {e} - Response Text: {response.text}")
            context = "Failed to parse context from LightRAG response."

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
            llm_response = call_deepseek_api(prompt)
            parsed_comments = 0
            for comment in llm_response.split('\n'):
                match = re.search(r'行\s*(\d+)\s*类型\s*([+-])\s*:\s*(.*)', comment)
                if match:
                    if parsed_comments < 3: # Ensure we don't exceed overall limit due to multiple diffs
                        line, line_type, comment_text = match.groups()
                        comments.append({"line": int(line), "file_path": new_file_path, "comment": comment_text, "line_type": line_type})
                        parsed_comments += 1
                    else:
                        break # Stop processing comments for this diff if limit reached
                else:
                    logger.warning(f"Failed to parse comment: {comment}")
            if parsed_comments == 0 and llm_response: # Log if LLM responded but no comments were parsed
                 logger.warning(f"LLM responded for {new_file_path}, but no comments were parsed. Response: {llm_response}")

        except Exception as e:
            logger.error(f"LLM analysis failed for {new_file_path}: {e}")
            # Avoid adding duplicate failure messages if multiple diffs fail
            if not any(c.get("comment", "") == "Code analysis failed, please review manually" and c.get("file_path") == new_file_path for c in comments):
                 comments.append({"line": 1, "file_path": new_file_path, "comment": "Code analysis failed, please review manually", "line_type": "+"})
            
    return comments[:3] # Apply overall limit again just in case

# ### 提交评论到 GitLab
def submit_comments_to_commit(project_id, sha, comments):
    """通过 GitLab API 提交评论到指定提交"""
    url = f"{GITLAB_URL}/projects/{project_id}/repository/commits/{sha}/comments"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    submitted_count = 0
    for comment in comments:
        if submitted_count >= 3: # Double check limit before posting
             logger.warning(f"Skipping additional comments for commit {sha} as limit of 3 is reached.")
             break
             
        line_type = "new" if comment["line_type"] == '+' else "old"
        payload = {
            "note": comment["comment"],
            "path": comment["file_path"],
            "line": comment["line"],
            "line_type": line_type
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 201:
                logger.info(f"Comment posted on line {comment['line']} of {comment['file_path']} with line_type {line_type}")
                submitted_count += 1
            else:
                logger.error(f"Failed to post comment: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            logger.error(f"Failed to submit comment: {e}")

# ### 主程序入口
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000) # Changed host to 0.0.0.0 for potential container usage