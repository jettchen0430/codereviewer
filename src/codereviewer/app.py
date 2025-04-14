from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from .config.settings import settings
from .utils.logger import logger
from .core.reviewer import reviewer

app = Flask(__name__)

# 验证配置
settings.validate()

# 定义线程池
executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """处理 GitLab Webhook 请求"""
    # 验证请求来源
    if request.headers.get('X-Gitlab-Token') != settings.WEBHOOK_SECRET:
        return jsonify({"error": "Invalid request source"}), 403
    
    # 验证请求数据
    data = request.json
    if not data or 'event_type' not in data:
        return jsonify({"error": "Invalid request data"}), 400
    
    # 处理 Merge Request 事件
    if data.get('event_type') == 'merge_request':
        mr_iid = data['object_attributes']['iid']
        project_id = data['project']['id']
        
        # 异步触发代码审查
        executor.submit(process_merge_request, project_id, mr_iid)
        
        return jsonify({"status": "success"}), 200
    
    return jsonify({"error": "Unsupported event type"}), 400

def process_merge_request(project_id: int, mr_iid: int):
    """处理 Merge Request 审查"""
    try:
        result = reviewer.review_merge_request(project_id, mr_iid)
        if result.success:
            logger.info(f"Successfully reviewed MR {mr_iid} in project {project_id}")
        else:
            logger.error(f"Failed to review MR {mr_iid} in project {project_id}: {result.error}")
    except Exception as e:
        logger.error(f"Error processing MR {mr_iid} in project {project_id}: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000) 