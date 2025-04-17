from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from src.codereviewer.config.settings import settings
from src.codereviewer.core.reviewer import code_reviewer
from src.codereviewer.utils.logger import setup_logger

# Initialize Flask app
app = Flask(__name__)

# Initialize logger
logger = setup_logger()

# Initialize thread pool
executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # Validate webhook secret
        if request.headers.get('X-GitLab-Token') != settings.WEBHOOK_SECRET:
            return jsonify({'error': 'Invalid webhook secret'}), 401

        # Get merge request data
        data = request.get_json()
        if not data or 'object_kind' not in data or data['object_kind'] != 'merge_request':
            return jsonify({'error': 'Invalid webhook data'}), 400

        # Process merge request asynchronously
        executor.submit(process_merge_request, data)
        return jsonify({'status': 'processing'}), 202

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_merge_request(data):
    try:
        # Get merge request details
        mr_id = data['object_attributes']['id']
        project_id = data['project']['id']

        # Review merge request
        code_reviewer.review_merge_request(project_id, mr_id)
        logger.info(f"Successfully reviewed merge request {mr_id}")

    except Exception as e:
        logger.error(f"Error processing merge request: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 