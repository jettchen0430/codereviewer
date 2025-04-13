from flask import Flask, request, jsonify
from threading import Thread
import requests
import openai
import json
import re
import os 
app = Flask(__name__)

# 配置 GitLab API
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
# 配置 DeepSeek API
#DEEPSEEK_URL = 'https://api.siliconflow.cn/v1/'
DEEPSEEK_URL = os.getenv("DEEPSEEK_URL")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """处理 GitLab Webhook 请求，异步触发代码审查"""
    data = request.json
    if data.get('event_type') == 'merge_request':
        mr_iid = data['object_attributes']['iid']
        project_id = data['project']['id']
        # 启动后台线程
        thread = Thread(target=trigger_review, args=(project_id, mr_iid))
        thread.start()
    return jsonify({"status": "success"}), 200

def trigger_review(project_id, mr_iid):
    """触发代码审查并提交评论"""
    mr_details = get_mr_details(project_id, mr_iid)
    if not mr_details:
        print("Failed to fetch MR details")
        return
    head_sha = mr_details.get('diff_refs', {}).get('head_sha')
    if not head_sha:
        print("Failed to get head_sha")
        return
    
    commit_diff = get_commit_diff(project_id, head_sha)
    if not commit_diff:
        print("Failed to fetch commit diff")
        return
    
    comments = analyze_code_with_llm(commit_diff)
    comments = comments[:3]  # 限制评论数量不超过 3 个
    
    submit_comments_to_commit(project_id, head_sha, comments)
    print(f"Reviewed commit {head_sha} in project {project_id}, submitted {len(comments)} comments")

def get_mr_details(project_id, mr_iid):
    """获取 Merge Request 的详细信息"""
    url = f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"Error fetching MR details: {response.status_code}")
    return None

def get_commit_diff(project_id, sha):
    """获取提交的 diff 数据"""
    url = f"{GITLAB_URL}/projects/{project_id}/repository/commits/{sha}/diff"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    print(f"Error fetching commit diff: {response.status_code}")
    return None

import re

def add_new_file_line_numbers(diff_str: str) -> str:
    """
    为 Git diff 中的每一行附上其在对应文件中的行号。
    - 对于上下文行和 +行，使用新文件中的行号。
    - 对于 -行，使用旧文件中的行号。
    - 对于 hunk header 行，标记为 "N/A"。

    Args:
        diff_str (str): Git diff 格式的字符串。

    Returns:
        str: 带有行号的 diff 字符串，每行以 "行号: 内容" 格式显示。
    """
    lines = diff_str.splitlines()
    result_lines = []
    current_old_line = None  # 当前旧文件的行号
    current_new_line = None  # 当前新文件的行号
    in_hunk = False          # 是否在 hunk 中

    for line in lines:
        # 匹配 hunk header，提取旧文件和新文件的起始行号
        hunk_match = re.match(r'@@ -(\d+),\d+ \+(\d+),\d+ @@', line)
        if hunk_match:
            start_old = int(hunk_match.group(1))  # 旧文件起始行号
            start_new = int(hunk_match.group(2))  # 新文件起始行号
            current_old_line = start_old
            current_new_line = start_new
            in_hunk = True
            result_lines.append(f"N/A: {line}")
            continue

        # 如果不在 hunk 中，跳过
        if not in_hunk:
            result_lines.append(f"N/A: {line}")
            continue

        # 处理 diff 的内容行
        if line.startswith('-'):
            # 旧文件中的删除行，分配旧文件行号并递增
            result_lines.append(f"{current_old_line}: {line}")
            current_old_line += 1
        elif line.startswith('+'):
            # 新文件中的添加行，分配新文件行号并递增
            result_lines.append(f"{current_new_line}: {line}")
            current_new_line += 1
        else:
            # 上下文行，在新旧文件中都存在，分配新文件行号并递增两个计数器
            result_lines.append(f"{current_new_line}: {line}")
            current_old_line += 1
            current_new_line += 1

    return "\n".join(result_lines)


def analyze_code_with_llm(commit_diff):
    """使用 DeepSeek R1 模型分析代码 diff 并生成评论"""
    comments = []
    for diff in commit_diff:
        new_file_path = diff.get('new_path', '')
        diff_content = diff.get('diff', '')
        f_diff = add_new_file_line_numbers(diff_content)

        prompt = f"""
        Analyze the following code diff, where each line is prefixed with its line number and type (e.g., '1: + code' or '2: - code'). 
        focusing only on the lines prefixed with '-' or '+'
        Provide up to 3 meaningful comments.
        Each comment should be in the strictly format "Line X Type Y: comment, original line code", 
        where 'X' is the original line number, 'Y' is the line type ('+' or '-'), and the comment is in 30 words.\n

        {f_diff}
        """
        
        payload = {
            "model": "deepseek-ai/DeepSeek-R1",
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
            "Authorization": DEEPSEEK_API_KEY,
            "Content-Type": "application/json"
        }
        response = requests.post(DEEPSEEK_URL, json=payload, headers=headers)
        response = json.loads(response.text)
        llm_response = response["choices"][0]["message"]["content"].strip()
        
        # 按行分割 LLM 响应
        llm_comments = llm_response.split('\n')
        
        for comment in llm_comments:
            # 去除行首的编号（如 "1. " 或 "2. "）
            comment = re.sub(r'^\d+\.\s*', '', comment.strip())
            # 匹配 "Line X Type Y: comment" 格式，忽略大小写并允许灵活的空格
            match = re.search(r'[Ll]ine\s*(\d+)\s*[Tt]ype\s*([+-])\s*:\s*(.*)', comment, re.IGNORECASE)
            if match:
                line = int(match.group(1))  # 提取行号
                line_type = match.group(2)  # 提取行类型 ('+' 或 '-')
                comment_text = match.group(3).strip()  # 提取评论内容
                comments.append({
                    "line": line,
                    "file_path": new_file_path,
                    "comment": comment_text,
                    "line_type": line_type  # 新增行类型字段
                })
            else:
                print(f"Failed to parse comment: {comment}")
                continue
    return comments[:3]

def submit_comments_to_commit(project_id, sha, comments):
    """通过 GitLab API 提交评论到指定提交"""
    url = f"{GITLAB_URL}/projects/{project_id}/repository/commits/{sha}/comments"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    for comment in comments:
        # 映射行类型为 GitLab API 所需的 "new" 或 "old"
        if comment["line_type"] == '+':
            line_type = "new"
        elif comment["line_type"] == '-':
            line_type = "old"
        else:
            line_type = "new"  # 默认值，适用于无明确类型的情况

        payload = {
            "note": comment["comment"],
            "path": comment["file_path"],
            "line": comment["line"],
            "line_type": line_type
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print(f"Comment posted on line {comment['line']} of {comment['file_path']} with line_type {line_type}")
        else:
            print(f"Failed to post comment: {response.status_code} - {response.text}")

if __name__ == "__main__":
    app.run(port=8000)