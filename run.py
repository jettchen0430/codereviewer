#!/usr/bin/env python3
"""
Code Reviewer 启动脚本
使用 LangChain 和 LangGraph 重构版本
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# 设置环境变量
os.environ.setdefault("FLASK_ENV", "production")

# 导入应用
from codereviewer.app import app
from codereviewer.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """主函数"""
    try:
        logger.info("Starting Code Reviewer application...")
        
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=8000,
            debug=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
