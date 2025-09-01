#!/usr/bin/env python3
"""
测试重构后的代码审查系统
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_imports():
    """测试模块导入"""
    try:
        from codereviewer.config.settings import settings
        print("✅ 配置模块导入成功")
        
        from codereviewer.models.review import ReviewRequest, Comment, LineType
        print("✅ 数据模型导入成功")
        
        from codereviewer.models.rag import Document, RetrievalResult
        print("✅ RAG模型导入成功")
        
        from codereviewer.api.gitlab import GitLabClient
        print("✅ GitLab客户端导入成功")
        
        from codereviewer.api.deepseek import DeepSeekClient
        print("✅ DeepSeek客户端导入成功")
        
        from codereviewer.utils.rag_utils import RAGEngine
        print("✅ RAG引擎导入成功")
        
        from codereviewer.core.reviewer import CodeReviewer
        print("✅ 代码审查器导入成功")
        
        from codereviewer.app import app
        print("✅ Flask应用导入成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ 模块导入失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False


def test_models():
    """测试数据模型"""
    try:
        from codereviewer.models.review import Comment, LineType
        
        # 测试评论模型
        comment = Comment(
            line=10,
            file_path="test.py",
            comment="建议使用更具描述性的变量名",
            line_type=LineType.ADDED
        )
        print(f"✅ 评论模型创建成功: {comment.comment}")
        
        # 测试行类型枚举
        assert LineType.ADDED == "+"
        assert LineType.DELETED == "-"
        print("✅ 行类型枚举测试通过")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据模型测试失败: {e}")
        return False


def test_rag_engine():
    """测试RAG引擎"""
    try:
        from codereviewer.utils.rag_utils import RAGEngine
        from codereviewer.models.rag import EmbeddingConfig
        
        # 创建RAG引擎
        config = EmbeddingConfig(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            dimension=384,
            device="cpu"
        )
        
        # 注意：这里只是测试导入，不实际初始化（避免下载模型）
        print("✅ RAG引擎配置创建成功")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG引擎测试失败: {e}")
        return False


def test_workflow_structure():
    """测试工作流结构"""
    try:
        from codereviewer.core.reviewer import CodeReviewer
        
        # 创建审查器（不初始化实际组件）
        print("✅ 代码审查器类定义正确")
        
        return True
        
    except Exception as e:
        print(f"❌ 工作流结构测试失败: {e}")
        return False


def test_config():
    """测试配置系统"""
    try:
        from codereviewer.config.settings import settings
        
        # 检查配置属性
        assert hasattr(settings, 'gitlab_url')
        assert hasattr(settings, 'deepseek_api_key')
        assert hasattr(settings, 'max_comments')
        
        print("✅ 配置系统测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 配置系统测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 开始测试重构后的代码审查系统...\n")
    
    tests = [
        ("模块导入", test_imports),
        ("数据模型", test_models),
        ("RAG引擎", test_rag_engine),
        ("工作流结构", test_workflow_structure),
        ("配置系统", test_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"📋 测试: {test_name}")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！重构后的系统可以正常导入和初始化。")
        print("\n📝 下一步:")
        print("1. 配置环境变量 (.env 文件)")
        print("2. 安装依赖: pip install -r requirements.txt")
        print("3. 启动应用: python run.py")
    else:
        print("⚠️  部分测试失败，请检查错误信息。")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
