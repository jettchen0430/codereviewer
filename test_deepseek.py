#!/usr/bin/env python3
"""
测试DeepSeek API连接
"""

import os
import sys
from dotenv import load_dotenv

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 加载环境变量
load_dotenv()

from codereviewer.api.deepseek import DeepSeekClient
from codereviewer.config.settings import settings

def test_deepseek_connection():
    """测试DeepSeek API连接"""
    print("🔍 测试DeepSeek API连接...")
    print(f"API URL: {settings.deepseek_url}")
    print(f"API Key: {settings.deepseek_api_key[:8]}...")
    
    try:
        client = DeepSeekClient()
        print(f"✓ DeepSeek客户端初始化成功")
        print(f"  模型: {client.model}")
        
        # 测试简单的代码分析
        test_diff = """@@ -0,0 +1,5 @@
+def hello_world():
+    print("Hello, World!")
+    return True
+"""
        
        print("\n📝 测试代码分析...")
        result = client.analyze_code_diff(test_diff)
        print(f"✓ 代码分析成功")
        print(f"  结果长度: {len(result)}")
        print(f"  结果预览: {result[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek API测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 DeepSeek API连接测试")
    print("=" * 50)
    
    if not settings.deepseek_api_key:
        print("❌ DEEPSEEK_API_KEY未设置")
        return
    
    if not settings.deepseek_url:
        print("❌ DEEPSEEK_URL未设置")
        return
    
    success = test_deepseek_connection()
    
    if success:
        print("\n🎉 DeepSeek API连接测试通过！")
    else:
        print("\n⚠️  DeepSeek API连接测试失败，请检查配置。")

if __name__ == "__main__":
    main()
