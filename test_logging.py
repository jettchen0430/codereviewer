#!/usr/bin/env python3
"""
测试脚本：验证logging输出是否包含LLM返回的comment
"""

import sys
import os
import logging

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from codereviewer.utils.logger import setup_logging, get_logger
from codereviewer.api.deepseek import DeepSeekClient

def test_llm_logging():
    """测试LLM logging输出"""
    
    # 设置日志
    setup_logging()
    logger = get_logger(__name__)
    
    logger.info("开始测试LLM logging输出")
    
    # 创建DeepSeek客户端
    client = DeepSeekClient()
    
    # 模拟一个简单的代码差异
    test_diff = """
@@ -1,3 +1,4 @@
 def hello_world():
-    print("Hello")
+    print("Hello World")
+    return True
"""
    
    # 测试代码分析
    logger.info("测试代码差异分析...")
    try:
        analysis = client.analyze_code_diff(test_diff)
        logger.info(f"分析结果: {analysis}")
    except Exception as e:
        logger.error(f"分析失败: {e}")
    
    # 测试摘要生成
    logger.info("测试摘要生成...")
    try:
        test_comments = [
            {"line": 1, "comment": "建议添加类型注解", "line_type": "+"},
            {"line": 2, "comment": "函数应该有返回值", "line_type": "+"}
        ]
        summary = client.generate_review_summary(test_comments)
        logger.info(f"摘要结果: {summary}")
    except Exception as e:
        logger.error(f"摘要生成失败: {e}")
    
    logger.info("测试完成")

if __name__ == "__main__":
    test_llm_logging()
