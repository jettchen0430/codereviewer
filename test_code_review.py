#!/usr/bin/env python3
"""
测试改进后的代码审查功能
"""

import os
import sys
from dotenv import load_dotenv

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 加载环境变量
load_dotenv()

from codereviewer.api.deepseek import DeepSeekClient
from codereviewer.core.reviewer import CodeReviewer
from codereviewer.config.settings import settings

def test_diff_line_numbering():
    """测试diff行号定位功能"""
    print("🔍 测试diff行号定位功能...")
    
    client = DeepSeekClient()
    
    # 测试diff内容
    test_diff = """@@ -0,0 +1,10 @@
+import sys
+import time
+from typing import List
+
+def main():
+    print("Hello, World!")
+    return True
+
+if __name__ == "__main__":
+    sys.exit(main())
"""
    
    # 测试行号定位
    formatted_diff = client._add_line_numbers_to_diff(test_diff)
    print("原始diff:")
    print(test_diff)
    print("\n格式化后的diff:")
    print(formatted_diff)
    
    return True

def test_code_review_prompt():
    """测试代码审查prompt构建"""
    print("\n🔍 测试代码审查prompt构建...")
    
    client = DeepSeekClient()
    
    test_diff = """@@ -0,0 +1,5 @@
+def hello_world():
+    print("Hello, World!")
+    return True
+"""
    
    prompt = client._build_code_review_prompt(test_diff, "测试上下文")
    print("生成的prompt:")
    print(prompt)
    
    return True

def test_comment_parsing():
    """测试评论解析功能"""
    print("\n🔍 测试评论解析功能...")
    
    reviewer = CodeReviewer()
    
    # 测试中文格式的评论
    chinese_analysis = """
行 1 类型 +: 函数缺少文档字符串，应添加描述函数用途和返回值的注释
行 2 类型 +: 硬编码字符串不利于国际化，建议使用配置文件或常量管理
行 3 类型 +: 返回值无实际意义，可移除或改为返回有意义的数据
"""
    
    # 测试英文格式的评论
    english_analysis = """
Line 1 Type +: Function missing docstring, should add comment describing purpose and return value
Line 2 Type +: Hardcoded string不利于国际化，建议使用配置文件或常量管理
Line 3 Type +: Return value has no practical meaning, can be removed or changed to meaningful data
"""
    
    print("测试中文格式评论解析:")
    chinese_comments = reviewer._parse_comments(chinese_analysis, "test.py")
    for comment in chinese_comments:
        print(f"  行 {comment.line} 类型 {comment.line_type}: {comment.comment}")
    
    print("\n测试英文格式评论解析:")
    english_comments = reviewer._parse_comments(english_analysis, "test.py")
    for comment in english_comments:
        print(f"  行 {comment.line} 类型 {comment.line_type}: {comment.comment}")
    
    return True

def main():
    """主函数"""
    print("🚀 代码审查功能测试")
    print("=" * 50)
    
    if not settings.deepseek_api_key:
        print("❌ DEEPSEEK_API_KEY未设置")
        return
    
    if not settings.deepseek_url:
        print("❌ DEEPSEEK_URL未设置")
        return
    
    try:
        # 测试diff行号定位
        test_diff_line_numbering()
        
        # 测试prompt构建
        test_code_review_prompt()
        
        # 测试评论解析
        test_comment_parsing()
        
        print("\n🎉 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
