from flask import Flask, request, jsonify
from threading import Thread
import requests
import json
import re
import os
import logging
import rag
import faiss
app = Flask(__name__)

with open('documents.txt', 'r', encoding='utf-8') as f:
    documents = [line.strip() for line in f.readlines()]
    
doc_embeddings = rag.get_embeddings(documents)
index = faiss.IndexFlatL2(doc_embeddings.shape[1])
index.add(doc_embeddings)
# 配置 GitLab API
GITLAB_URL = os.getenv("GITLAB_URL")
GITLAB_TOKEN = os.getenv("GITLAB_TOKEN")
# 配置 DeepSeek API
DEEPSEEK_URL = os.getenv("DEEPSEEK_URL")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# 配置日志
logging.basicConfig(level=logging.INFO, filename="reviewer.log",format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 定义全局缓存字典
diff_cache = {}

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
    
    # 缓存 diff_content
    for diff in commit_diff:
        diff_content = diff.get('diff', '')
        diff_cache[(project_id, head_sha, diff.get('new_path', ''))] = diff_content
    
    comments = analyze_code_with_llm(commit_diff)
    if not comments:
        logger.warning("No comments generated, retrying with cached diff")
        comments = retry_analyze_code_with_llm(project_id, head_sha)
    
    comments = comments[:3]  # 限制评论数量不超过 3 个
    submit_comments_to_commit(project_id, head_sha, comments)
    logger.info(f"Reviewed commit {head_sha} in project {project_id}, submitted {len(comments)} comments")

def get_mr_details(project_id, mr_iid):
    """获取 Merge Request 的详细信息"""
    url = f"{GITLAB_URL}/projects/{project_id}/merge_requests/{mr_iid}"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    logger.error(f"Error fetching MR details: {response.status_code}")
    return None

def get_commit_diff(project_id, sha):
    """获取提交的 diff 数据"""
    url = f"{GITLAB_URL}/projects/{project_id}/repository/commits/{sha}/diff"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    logger.error(f"Error fetching commit diff: {response.status_code}")
    return None

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
            start_old = int(hunk_match.group(1))
            start_new = int(hunk_match.group(2))
            current_old_line = start_old
            current_new_line = start_new
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

def analyze_code_with_llm(commit_diff):
    """使用 DeepSeek R1 模型分析代码 diff 并生成评论"""
    comments = []
    for diff in commit_diff:
        new_file_path = diff.get('new_path', '')
        diff_content = diff.get('diff', '')
        f_diff = add_new_file_line_numbers(diff_content)
        retrieved_docs = rag.retrieve(diff_content, k=2)  # 检索 2 个最相关文档
        context = "\n".join(retrieved_docs)

        prompt = f"""
        Analyze the following code diff, where each line is prefixed with its line number and type (e.g., '1: + code' or '2: - code'). 
        focusing only on the lines prefixed with '-' or '+'
        Provide up to 3 meaningful comments.
        Each comment should be in the strictly format "Line X Type Y: comment, original line code", 
        where 'X' is the original line number, 'Y' is the line type ('+' or '-'), and the comment is in 30 words.\n
        Additionally, consider the following relevant documents to enhance your analysis:
        {context}

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
                {"role": "user", "content": prompt}
            ]
        }
        headers = {
            "Authorization": DEEPSEEK_API_KEY,
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(DEEPSEEK_URL, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            llm_response = response_data["choices"][0]["message"]["content"].strip()
            
            llm_comments = llm_response.split('\n')
            for comment in llm_comments:
                comment = re.sub(r'^\d+\.\s*', '', comment.strip())
                match = re.search(r'[Ll]ine\s*(\d+)\s*[Tt]ype\s*([+-])\s*:\s*(.*)', comment, re.IGNORECASE)
                if match:
                    line = int(match.group(1))
                    line_type = match.group(2)
                    comment_text = match.group(3).strip()
                    comments.append({
                        "line": line,
                        "file_path": new_file_path,
                        "comment": comment_text,
                        "line_type": line_type
                    })
                else:
                    logger.warning(f"Failed to parse comment: {comment}")
        except requests.RequestException as e:
            logger.error(f"Request to DeepSeek API failed: {e}")
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse response: {e}")
    return comments[:3]

def retry_analyze_code_with_llm(project_id, sha):
    """使用缓存的 diff_content 重新分析代码"""
    comments = []
    for key in diff_cache:
        if key[0] == project_id and key[1] == sha:
            diff_content = diff_cache[key]
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
                "messages": [{"role": "user", "content": prompt}]
            }
            headers = {
                "Authorization": DEEPSEEK_API_KEY,
                "Content-Type": "application/json"
            }
            try:
                response = requests.post(DEEPSEEK_URL, json=payload, headers=headers)
                response.raise_for_status()
                response_data = response.json()
                llm_response = response_data["choices"][0]["message"]["content"].strip()
                llm_comments = llm_response.split('\n')
                for comment in llm_comments:
                    comment = re.sub(r'^\d+\.\s*', '', comment.strip())
                    match = re.search(r'[Ll]ine\s*(\d+)\s*[Tt]ype\s*([+-])\s*:\s*(.*)', comment, re.IGNORECASE)
                    if match:
                        line = int(match.group(1))
                        line_type = match.group(2)
                        comment_text = match.group(3).strip()
                        comments.append({
                            "line": line,
                            "file_path": key[2],  # new_path
                            "comment": comment_text,
                            "line_type": line_type
                        })
            except requests.RequestException as e:
                logger.error(f"Retry request to DeepSeek API failed: {e}")
            except (KeyError, IndexError) as e:
                logger.error(f"Failed to parse retry response: {e}")
    return comments[:3]

def submit_comments_to_commit(project_id, sha, comments):
    """通过 GitLab API 提交评论到指定提交"""
    url = f"{GITLAB_URL}/projects/{project_id}/repository/commits/{sha}/comments"
    headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}
    for comment in comments:
        line_type = "new" if comment["line_type"] == '+' else "old"
        payload = {
            "note": comment["comment"],
            "path": comment["file_path"],
            "line": comment["line"],
            "line_type": line_type
        }
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 201:
            logger.info(f"Comment posted on line {comment['line']} of {comment['file_path']} with line_type {line_type}")
        else:
            logger.error(f"Failed to post comment: {response.status_code} - {response.text}")

if __name__ == "__main__":
    app.run(port=8000)