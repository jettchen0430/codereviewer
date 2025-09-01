from flask import Flask, request, jsonify
from threading import Thread
import logging
from .core.reviewer import code_reviewer
from .utils.logger import get_logger
from .config.settings import settings

logger = get_logger(__name__)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    """根路径 - 显示API信息"""
    return jsonify({
        "service": "Code Reviewer API",
        "version": "2.0.0",
        "description": "AI-powered code review service for GitLab merge requests",
        "endpoints": {
            "GET /": "This endpoint - API information",
            "GET /health": "Health check endpoint",
            "POST /webhook": "GitLab webhook handler for merge requests",
            "POST /review/<project_id>/<mr_iid>": "Manual code review trigger",
            "GET /status/<project_id>/<mr_iid>": "Get review status",
            "GET /config": "Get current configuration"
        },
        "usage": "Send POST requests to /webhook for automatic reviews or use /review for manual reviews"
    }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "service": "code-reviewer",
        "version": "2.0.0"
    }), 200


@app.route('/webhook', methods=['POST'])
def handle_webhook():
    """处理 GitLab Webhook 请求"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400
        
        # 验证webhook事件类型
        event_type = data.get('event_type')
        if event_type != 'merge_request':
            return jsonify({"status": "ignored", "reason": f"Event type {event_type} not supported"}), 200
        
        # 验证webhook签名（可选）
        if not _validate_webhook_signature(request):
            logger.warning("Invalid webhook signature")
            return jsonify({"error": "Invalid signature"}), 401
        
        # 提取MR信息
        mr_data = data.get('object_attributes', {})
        project_id = data.get('project', {}).get('id')
        mr_iid = mr_data.get('iid')
        
        if not all([project_id, mr_iid]):
            return jsonify({"error": "Missing required MR information"}), 400
        
        # 检查MR状态
        mr_state = mr_data.get('state')
        if mr_state not in ['opened', 'reopened']:
            return jsonify({"status": "ignored", "reason": f"MR state {mr_state} not supported"}), 200
        
        # 异步触发代码审查
        thread = Thread(
            target=_trigger_code_review,
            args=(project_id, mr_iid),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Started code review for MR {mr_iid} in project {project_id}")
        return jsonify({
            "status": "success",
            "message": f"Code review started for MR {mr_iid}",
            "project_id": project_id,
            "mr_iid": mr_iid
        }), 202
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/review/<int:project_id>/<int:mr_iid>', methods=['POST'])
def manual_review(project_id: int, mr_iid: int):
    """手动触发代码审查"""
    try:
        logger.info(f"Manual review requested for MR {mr_iid} in project {project_id}")
        
        # 执行代码审查
        result = code_reviewer.review(project_id, mr_iid)
        
        return jsonify({
            "status": "success",
            "result": {
                "request_id": result.request_id,
                "merge_request_id": result.merge_request_id,
                "comments_count": len(result.comments),
                "summary": result.summary,
                "status": result.status,
                "processing_time": result.processing_time
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Manual review failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/status/<int:project_id>/<int:mr_iid>', methods=['GET'])
def get_review_status(project_id: int, mr_iid: int):
    """获取审查状态"""
    try:
        # 这里可以实现状态查询逻辑
        # 暂时返回基本信息
        return jsonify({
            "project_id": project_id,
            "mr_iid": mr_iid,
            "status": "unknown",
            "message": "Status tracking not implemented yet"
        }), 200
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/config', methods=['GET'])
def get_config():
    """获取当前配置信息"""
    try:
        config_info = {
            "gitlab_url": settings.gitlab_url,
            "deepseek_url": settings.deepseek_url,
            "max_workers": settings.max_workers,
            "max_comments": settings.max_comments,
            "api_timeout": settings.api_timeout,
            "retry_attempts": settings.retry_attempts,
            "retry_delay": settings.retry_delay,
            "embedding_dimension": settings.embedding_dimension,
            "max_retrieved_docs": settings.max_retrieved_docs
        }
        
        return jsonify({
            "status": "success",
            "config": config_info
        }), 200
        
    except Exception as e:
        logger.error(f"Config retrieval failed: {e}")
        return jsonify({"error": str(e)}), 500


def _validate_webhook_signature(request) -> bool:
    """验证webhook签名"""
    if not settings.webhook_secret:
        # 如果没有配置密钥，跳过验证
        return True
    
    # 这里应该实现实际的签名验证逻辑
    # 为了简化，暂时返回True
    return True


def _trigger_code_review(project_id: int, mr_iid: int):
    """触发代码审查"""
    try:
        logger.info(f"Starting code review for MR {mr_iid} in project {project_id}")
        
        # 执行代码审查
        result = code_reviewer.review(project_id, mr_iid)
        
        if result.status == "completed":
            logger.info(f"Code review completed for MR {mr_iid}: {len(result.comments)} comments generated")
        else:
            logger.error(f"Code review failed for MR {mr_iid}: {result.summary}")
            
    except Exception as e:
        logger.error(f"Code review failed for MR {mr_iid}: {e}")


@app.errorhandler(404)
def not_found(error):
    """处理404错误"""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """处理500错误"""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    logger.info("Starting Code Reviewer application...")
    
    # 验证必要的配置
    required_configs = [
        ("GITLAB_URL", settings.gitlab_url),
        ("GITLAB_TOKEN", settings.gitlab_token),
        ("DEEPSEEK_URL", settings.deepseek_url),
        ("DEEPSEEK_API_KEY", settings.deepseek_api_key)
    ]
    
    missing_configs = [name for name, value in required_configs if not value]
    if missing_configs:
        logger.error(f"Missing required configuration: {', '.join(missing_configs)}")
        exit(1)
    
    logger.info("Configuration validation passed")
    
    # 启动应用
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=False
    ) 