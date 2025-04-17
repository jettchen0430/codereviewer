from flask import Flask, request, jsonify
from celery import Celery
import requests
import openai

app = Flask(__name__)

# 配置 GitLab API
GITLAB_URL = "https://gitlab.com/api/v4"  # 替换为你的 GitLab 实例 URL
GITLAB_TOKEN = "glpat-T8yrGPyHyxMGA3ocHAAh"  # 替换为你的 GitLab Personal Access Token

# 配置 Celery
celery = Celery('tasks', broker='amqp://guest:guest@localhost:5672//')  # 使用 Redis 作为消息代理

# 配置 DeepSeek API
DEEPSEEK_URL = 'https://api.siliconflow.cn/v1/'
DEEPSEEK_API_KEY = 'sk-cvgoxanixhgfrsbydseueinknvwfragexkfaqnyhhngnxbkv'

client = openai.OpenAI(
    base_url=DEEPSEEK_URL,
    api_key=DEEPSEEK_API_KEY
)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """处理 GitLab Webhook 请求，异步触发代码审查"""
    data = request.json
    if data.get('event_type') == 'merge_request':
        mr_iid = data['object_attributes']['iid']  # 获取 MR 的内部 ID
        project_id = data['project']['id']         # 获取项目 ID
        # 异步调用 Celery 任务
        trigger_review.delay(project_id, mr_iid)
    return jsonify({"status": "success"}), 200

@celery.task
def trigger_review(project_id, mr_iid):
    """异步任务：触发代码审查并提交评论"""
    # 获取 MR 的详细信息，获取 head_sha
    mr_details = get_mr_details(project_id, mr_iid)
    if not mr_details:
        print("Failed to fetch MR details")
        return
    head_sha = mr_details.get('diff_refs', {}).get('head_sha')
    if not head_sha:
        print("Failed to get head_sha")
        return
    
    # 获取提交的 diff
    commit_diff = get_commit_diff(project_id, head_sha)
    if not commit_diff:
        print("Failed to fetch commit diff")
        return
    
    # 使用 LLM 分析代码
    comments = analyze_code_with_llm(commit_diff)
    
    # 限制评论数量不超过 3 个
    comments = comments[:3]
    
    # 提交评论到提交
    submit_comments_to_commit(project_id, head_sha, comments)
    print(f"Reviewed commit {head_sha} in project {project_id}, submitted {len(comments)} comments")

def get_mr_details(project_id, mr_iid):
    """获取 Merge Request 的详细信息"""
    url = f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching MR details: {response.status_code}")
        return None

def get_commit_diff(project_id, sha):
    """获取提交的 diff 数据"""
    url = f"{GITLAB_URL}/projects/{project_id}/repository/commits/{sha}/diff"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching commit diff: {response.status_code}")
        return None

def analyze_code_with_llm(commit_diff):
    """使用 DeepSeek R1 模型分析代码 diff 并生成评论"""
    comments = []
    for diff in commit_diff:
        new_file_path = diff.get('new_path', '')  # 获取文件路径
        diff_content = diff.get('diff', '')       # 获取 diff 内容

        # 构建提示
        prompt = f"""
Analyze the following code diff and provide up to 3 meaningful comments.
Each comment should be in the format "Line X: comment", where X is the line number in the new file.

{diff_content}
"""

        # 调用 DeepSeek R1 模型
        messages = [{"role": "user", "content": prompt}]
        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1",
            messages=messages,
            stream=False,
            max_tokens=150,
            temperature=0.5
        )

        # 解析 LLM 响应
        llm_response = response.choices[0].message.content.strip()
        llm_comments = llm_response.split('\n')

        # 提取最多 3 条评论
        for comment in llm_comments[:3]:
            try:
                line_str, comment_text = comment.split(':', 1)  # 分割行号和评论
                line = int(line_str.replace('Line ', ''))       # 提取行号
                comments.append({
                    "line": line,
                    "file_path": new_file_path,
                    "comment": comment_text.strip()
                })
            except:
                continue

    return comments[:3]  # 确保返回不超过 3 条评论

def submit_comments_to_commit(project_id, sha, comments):
    """通过 GitLab API 提交评论到指定提交"""
    url = f"{GITLAB_URL}/projects/{project_id}/repository/commits/{sha}/comments"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    for comment in comments:
        payload = {
            "note": comment["comment"],
            "path": comment["file_path"],
            "line": comment["line"],
            "line_type": "new"
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print(f"Comment posted on line {comment['line']} of {comment['file_path']}")
        else:
            print(f"Failed to post comment: {response.status_code} - {response.text}")

if __name__ == "__main__":
    app.run(port=8000)