from flask import Flask, request, jsonify
import requests
import random  # 用于模拟简单代码分析
import openai

app = Flask(__name__)

# 配置 GitLab API
GITLAB_URL = "https://gitlab.com/api/v4"  # 替换为你的 GitLab 实例 URL
GITLAB_TOKEN = "glpat-T8yrGPyHyxMGA3ocHAAh"  # 替换为你的 GitLab Personal Access Token

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    data = request.json
    if data.get('event_type') == 'merge_request':
        mr_iid = data['object_attributes']['iid']  # 获取 MR 的内部 ID
        project_id = data['project']['id']         # 获取项目 ID
        trigger_review(project_id, mr_iid)
    return jsonify({"status": "success"}), 200

def trigger_review(project_id, mr_iid):
    # 获取 MR 的详细信息，包括 diff
    mr_diff = get_mr_diff(project_id, mr_iid)
    if not mr_diff:
        print("Failed to fetch MR diff")
        return
    
    # 分析代码并生成评论
    comments = analyze_code(mr_diff)  # 可替换为 analyze_code_with_llm(mr_diff)
    
    # 限制评论数量不超过 3 个
    comments = comments[:3]
    
    # 提交评论到 GitLab MR
    submit_comments(project_id, mr_iid, comments)
    print(f"Reviewed MR {mr_iid} in project {project_id}, submitted {len(comments)} comments")

def get_mr_diff(project_id, mr_iid):
    # 调用 GitLab API 获取 MR 的 diff
    url = f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}/diffs"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching diff: {response.status_code}")
        return None

def analyze_code(mr_diff):
    comments = []
    for diff in mr_diff:
        new_file_path = diff['new_path']
        diff_content = diff['diff']
        lines = diff_content.splitlines()
        new_line = 0  # 新文件中的行号
        for line in lines:
            if line.startswith('@@'):
                # 解析 hunk 头部，例如 @@ -1,3 +1,4 @@
                parts = line.split()
                new_start = int(parts[2].split(',')[0][1:])  # +1,4 -> 1
                new_line = new_start
                continue
            if line.startswith('+'):
                code_line = line[1:].strip()
                # 示例规则：检查缺少注释
                if 'def ' in code_line and '#' not in code_line:
                    comments.append({
                        "line": new_line,
                        "file_path": new_file_path,
                        "comment": "建议为函数添加注释，说明功能和参数。"
                    })
                new_line += 1
            elif line.startswith(' '):
                new_line += 1
            # 如果是 '-' 开头，不影响 new_line
    return comments[:3]

def submit_comments(project_id, mr_iid, comments):
    # 通过 GitLab Discussion API 提交评论到对应代码行
    url = f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}/discussions"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    
    for comment in comments:
        payload = {
            "body": comment["comment"],
            "position": {
                "base_sha": get_mr_base_sha(project_id, mr_iid),
                "start_sha": get_mr_start_sha(project_id, mr_iid),
                "head_sha": get_mr_head_sha(project_id, mr_iid),
                "position_type": "text",
                "new_path": comment["file_path"],
                "new_line": comment["line"]  # diff 中的行号
            }
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            print(f"Comment posted on line {comment['line']} of {comment['file_path']}")
        else:
            print(f"Failed to post comment: {response.status_code} - {response.text}")

def get_mr_base_sha(project_id, mr_iid):
    # 获取 MR 的 base SHA
    url = f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    return response.json().get('diff_refs', {}).get('base_sha', '') if response.status_code == 200 else ""

def get_mr_start_sha(project_id, mr_iid):
    # 获取 MR 的 start SHA
    url = f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    return response.json().get('diff_refs', {}).get('start_sha', '') if response.status_code == 200 else ""

def get_mr_head_sha(project_id, mr_iid):
    # 获取 MR 的 head SHA
    url = f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    return response.json().get('diff_refs', {}).get('head_sha', '') if response.status_code == 200 else ""

# 可选：使用 LLM 分析代码
def analyze_code_with_llm(mr_diff):
    comments = []
    for diff in mr_diff:
        new_file_path = diff.get('new_path', '')
        diff_content = diff.get('diff', '')
        # 构造 LLM 提示
        prompt = f"Analyze this code diff and provide up to 3 meaningful comments:\n{diff_content}"
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=150
        )
        llm_comments = response.choices[0].text.strip().split('\n')
        for comment in llm_comments[:3]:  # 限制最多 3 条
            try:
                # 假设 LLM 返回格式为 "Line X: comment"
                line_str, comment_text = comment.split(':', 1)
                line = int(line_str.replace('Line ', ''))
                comments.append({
                    "line": line,
                    "file_path": new_file_path,
                    "comment": comment_text.strip()
                })
            except:
                continue
    return comments[:3]

if __name__ == "__main__":
    app.run(port=8000)