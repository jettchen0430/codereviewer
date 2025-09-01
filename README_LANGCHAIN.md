# Code Reviewer - LangChain & LangGraph 重构版本

这是一个使用 LangChain 和 LangGraph 重构的智能代码审查系统，集成 GitLab 并使用 DeepSeek API 进行自动代码分析。

## 🚀 新特性

### LangChain 集成
- **智能工作流**: 使用 LangGraph 构建可配置的代码审查工作流
- **状态管理**: 基于状态图的审查流程，支持复杂的审查逻辑
- **模块化设计**: 每个审查步骤都是独立的节点，易于扩展和修改

### 改进的架构
- **类型安全**: 使用 Pydantic 模型确保数据一致性
- **异步处理**: 支持并发审查请求
- **错误恢复**: 内置重试机制和错误处理
- **配置管理**: 基于环境变量的灵活配置

### 增强的 RAG 系统
- **向量检索**: 使用 FAISS 进行高效的相似度搜索
- **知识库管理**: 支持动态添加和更新审查指导原则
- **上下文增强**: 基于检索结果提供更准确的审查建议

## 🏗️ 项目结构

```
codereviewer/
├── src/
│   └── codereviewer/
│       ├── api/                    # API 客户端
│       │   ├── gitlab.py          # GitLab API 客户端
│       │   └── deepseek.py        # DeepSeek API 客户端
│       ├── config/                 # 配置管理
│       │   └── settings.py        # 应用配置
│       ├── core/                   # 核心逻辑
│       │   └── reviewer.py        # 代码审查器（LangGraph 工作流）
│       ├── models/                 # 数据模型
│       │   ├── review.py          # 审查相关模型
│       │   └── rag.py             # RAG 相关模型
│       ├── utils/                  # 工具函数
│       │   ├── rag_utils.py       # RAG 引擎
│       │   └── logger.py          # 日志工具
│       └── app.py                 # Flask 应用
├── run.py                         # 启动脚本
├── env.example                    # 环境变量示例
├── requirements.txt               # 项目依赖
└── README_LANGCHAIN.md           # 本文档
```

## 🛠️ 安装和配置

### 1. 克隆项目
```bash
git clone <repository-url>
cd codereviewer
```

### 2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
```bash
cp env.example .env
# 编辑 .env 文件，填入你的配置
```

### 5. 启动应用
```bash
python run.py
```

## 🔧 配置说明

### 必需配置
- `GITLAB_URL`: GitLab 实例 URL
- `GITLAB_TOKEN`: GitLab API 令牌
- `DEEPSEEK_URL`: DeepSeek API 端点
- `DEEPSEEK_API_KEY`: DeepSeek API 密钥

### 可选配置
- `WEBHOOK_SECRET`: Webhook 签名密钥
- `MAX_WORKERS`: 最大并发工作线程数
- `MAX_COMMENTS`: 每次审查的最大评论数
- `EMBEDDING_DIMENSION`: 嵌入向量维度
- `MAX_RETRIEVED_DOCS`: 最大检索文档数

## 🔄 工作流程

### LangGraph 工作流节点

1. **extract_context**: 提取审查上下文
   - 获取项目信息
   - 检索相关知识库内容

2. **analyze_diffs**: 分析代码差异
   - 解析 diff 内容
   - 提取行号信息

3. **generate_comments**: 生成审查评论
   - 调用 DeepSeek API 分析代码
   - 解析生成的评论

4. **post_comments**: 发布评论
   - 将评论提交到 GitLab
   - 处理不同类型的行（新增/删除）

5. **generate_summary**: 生成审查摘要
   - 总结审查结果
   - 提供改进建议

## 📡 API 端点

### Webhook 端点
- `POST /webhook`: 处理 GitLab webhook 请求

### 手动审查
- `POST /review/<project_id>/<mr_iid>`: 手动触发代码审查

### 状态查询
- `GET /status/<project_id>/<mr_iid>`: 获取审查状态

### 系统信息
- `GET /health`: 健康检查
- `GET /config`: 获取当前配置

## 🧠 RAG 系统

### 知识库管理
系统维护一个代码审查最佳实践的知识库，包括：
- 代码质量标准
- 常见问题识别
- 改进建议模板

### 检索增强
- 基于代码变更内容检索相关知识
- 将检索结果作为上下文提供给 LLM
- 生成更准确和相关的审查建议

## 🔍 使用示例

### 1. 自动审查（通过 Webhook）
当 GitLab 中创建或更新合并请求时，系统会自动：
1. 接收 webhook 通知
2. 提取代码变更
3. 执行智能审查
4. 生成并发布评论

### 2. 手动审查
```bash
curl -X POST http://localhost:8000/review/123/456
```

### 3. 检查状态
```bash
curl http://localhost:8000/status/123/456
```

## 🚀 扩展和定制

### 添加新的审查节点
```python
def custom_analysis_node(state: ReviewRequest) -> ReviewRequest:
    # 自定义分析逻辑
    return state

# 在工作流中添加节点
workflow.add_node("custom_analysis", custom_analysis_node)
```

### 自定义 RAG 检索
```python
# 在 rag_utils.py 中添加新的检索策略
def semantic_search(query: str, documents: List[Document]) -> List[Document]:
    # 实现语义搜索逻辑
    pass
```

### 集成其他 LLM
```python
# 在 deepseek.py 中添加新的 LLM 客户端
class CustomLLMClient:
    def analyze_code_diff(self, diff_content: str) -> str:
        # 实现自定义 LLM 调用
        pass
```

## 📊 监控和日志

### 日志级别
- `DEBUG`: 详细的调试信息
- `INFO`: 一般操作信息
- `WARNING`: 警告消息
- `ERROR`: 错误消息

### 性能指标
- 审查处理时间
- 评论生成数量
- API 调用成功率
- 错误率统计

## 🔒 安全特性

- Webhook 签名验证
- API 密钥管理
- 请求频率限制
- 错误信息脱敏

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。

## 🙏 致谢

- [LangChain](https://langchain.com/) - LLM 应用开发框架
- [LangGraph](https://langchain.com/langgraph) - 工作流编排工具
- [GitLab API](https://docs.gitlab.com/ee/api/) - GitLab 集成
- [DeepSeek API](https://deepseek.com/api) - AI 代码分析
- [FAISS](https://github.com/facebookresearch/faiss) - 向量检索
- [Sentence Transformers](https://www.sbert.net/) - 文本嵌入
