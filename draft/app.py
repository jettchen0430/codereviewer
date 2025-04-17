from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import requests
import openai
import json
import re
import logging
from tenacity import retry, stop_after_attempt, wait_fixed
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO, filename='reviewer.log', 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 配置 GitLab API
GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.com/api/v4")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")

# 配置 DeepSeek API
DEEPSEEK_URL = os.getenv("DEEPSEEK_URL", "https://api.siliconflow.cn/v1/chat/completions")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Webhook 验证 Token
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN")

# LLM 模型选择
MODEL_MAP = {
    "deepseek": "deepseek-ai/DeepSeek-V3",
    # 可扩展支持其他模型，例如 "openai": "gpt-4"
}
selected_model = os.getenv("LLM_MODEL", "deepseek")

# 自定义 Prompt
DEFAULT_PROMPT = "Analyze the diff and provide up to 3 comments in format 'Line X: comment':\n{diff}"
prompt_template = os.getenv("CUSTOM_PROMPT", DEFAULT_PROMPT)

# 初始化 OpenAI 客户端
client = openai.OpenAI(
    base_url=DEEPSEEK_URL,
    api_key=DEEPSEEK_API_KEY
)

# 初始化 Flask 应用
app = Flask(__name__)

# 线程池，限制最大并发线程数
executor = ThreadPoolExecutor(max_workers=5)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """处理 GitLab Webhook 请求，异步触发代码审查"""
    token = request.headers.get('X-Gitlab-Token')
    if token != WEBHOOK_TOKEN:
        logger.warning("Invalid Webhook token")
        return jsonify({"error": "Invalid token"}), 403
    
    data = request.json
    if data.get('event_type') == 'merge_request':
        mr_iid = data['object_attributes']['iid']
        project_id = data['project']['id']
        executor.submit(trigger_review, project_id, mr_iid)
    return jsonify({"status": "success"}), 200

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

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_mr_details(project_id, mr_iid):
    """获取 Merge Request 的详细信息"""
    url = f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logger.info(f"Fetched MR details for project {project_id}, MR {mr_iid}")
        return response.json()
    logger.error(f"Failed to fetch MR details: {response.status_code}")
    return None

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_commit_diff(project_id, sha):
    """获取提交的 diff 数据"""
    url = f"{GITLAB_URL}/projects/{project_id}/repository/commits/{sha}/diff"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        logger.info(f"Fetched commit diff for project {project_id}, commit {sha}")
        return response.json()
    logger.error(f"Failed to fetch commit diff: {response.status_code}")
    return None

def analyze_code_with_llm(commit_diff):
    """使用 LLM 模型分析代码 diff 并生成评论"""
    comments = []
    seen_comments = set()
    for diff in commit_diff:
        new_file_path = diff.get('new_path', '')
        diff_content = diff.get('diff', '')
        
        prompt = prompt_template.format(diff=diff_content)
        
        payload = {
            "model": MODEL_MAP[selected_model],
            "stream": False,
            "max_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.7,
            "top_k": 50,
            "frequency_penalty": 0.5,
            "n": 1,
            "stop": [],
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(DEEPSEEK_URL, json=payload, headers=headers)
            response.raise_for_status()
            llm_response = response.json()["choices"][0]["message"]["content"].strip()
            
            # 按行分割 LLM 响应
            llm_comments = llm_response.split('\n')
            
            for comment in llm_comments:
                # 去除行首的编号
                comment = re.sub(r'^\d+\.\s*', '', comment.strip())
                # 匹配 "Line X: comment" 格式
                match = re.search(r'[Ll]ine\s*(\d+)\s*:\s*(.*)', comment, re.IGNORECASE)
                if match:
                    line, text = int(match.group(1)), match.group(2).strip()
                    if len(text) < 10 or (line, text) in seen_comments:
                        continue
                    seen_comments.add((line, text))
                    comments.append({"line": line, "file_path": new_file_path, "comment": text})
        except Exception as e:
            logger.error(f"Failed to analyze diff: {e}")
    return comments[:3]

def submit_comments_to_commit(project_id, sha, comments):
    """通过 GitLab API 提交评论到指定提交"""
    url = f"{GITLAB_URL}/projects/{project_id}/repository/commits/{sha}/comments"
    headers ={"PRIVATE-TOKEN": GITLAB_TOKEN}
    for comment in comments:
        payload = {
            "note": comment["comment"],
            "path": comment["file_path"],
            "line": comment["line"],
            "line_type": "new"
        }
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 201:
                logger.info(f"Comment posted on line {comment['line']} of {comment['file_path']}")
            else:
                logger.error(f"Failed to post comment: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"Exception while posting comment: {e}")

if __name__ == "__main__":
    app.run(port=8000)