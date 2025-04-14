# Automated Code Review System / 自动代码审查系统

[English](README.en.md) | [中文](README.zh.md)

An intelligent code review system that integrates with GitLab and uses DeepSeek API for automated code analysis. The system leverages RAG (Retrieval-Augmented Generation) to provide context-aware code review suggestions.

一个智能的代码审查系统，集成 GitLab 并使用 DeepSeek API 进行自动代码分析。系统利用 RAG（检索增强生成）技术提供上下文感知的代码审查建议。

Please select your preferred language from the links above to view the full documentation.

请从上方的链接选择您偏好的语言来查看完整文档。

## Features / 功能特点

- 🤖 **Automated Code Review**: Automatically reviews code changes in GitLab merge requests
  **自动代码审查**：自动审查 GitLab 合并请求中的代码变更

- 🧠 **AI-Powered Analysis**: Uses DeepSeek API for intelligent code analysis
  **AI 驱动分析**：使用 DeepSeek API 进行智能代码分析

- 📚 **RAG Integration**: Leverages document retrieval to provide context-aware suggestions
  **RAG 集成**：利用文档检索提供上下文感知的建议

- 🔄 **Asynchronous Processing**: Handles multiple review requests concurrently
  **异步处理**：并发处理多个审查请求

- 📝 **Configurable Settings**: Easy configuration through environment variables
  **可配置设置**：通过环境变量轻松配置

- 📊 **Comprehensive Logging**: Detailed logging for monitoring and debugging
  **全面日志记录**：详细的日志记录用于监控和调试

- 🔒 **Secure Webhook Handling**: Validates GitLab webhook requests
  **安全的 Webhook 处理**：验证 GitLab webhook 请求

- 🔄 **Retry Mechanism**: Automatic retry for failed API calls
  **重试机制**：API 调用失败时自动重试

- 💾 **Caching System**: Efficient diff caching for improved performance
  **缓存系统**：高效的 diff 缓存以提高性能

## Project Structure / 项目结构

```
codereviewer/
├── src/
│   └── codereviewer/
│       ├── api/
│       │   ├── __init__.py
│       │   ├── deepseek.py      # DeepSeek API client / DeepSeek API 客户端
│       │   └── gitlab.py        # GitLab API client / GitLab API 客户端
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py      # Configuration settings / 配置设置
│       ├── core/
│       │   ├── __init__.py
│       │   └── reviewer.py      # Core review logic / 核心审查逻辑
│       ├── models/
│       │   ├── __init__.py
│       │   ├── review.py        # Review-related models / 审查相关模型
│       │   └── rag.py           # RAG-related models / RAG 相关模型
│       ├── utils/
│       │   ├── __init__.py
│       │   ├── diff_utils.py    # Diff processing utilities / Diff 处理工具
│       │   ├── logger.py        # Logging utilities / 日志工具
│       │   └── rag_utils.py     # RAG utilities / RAG 工具
│       ├── __init__.py
│       └── app.py              # Main application / 主应用程序
├── tests/
│   └── __init__.py
├── .env.example               # Example environment variables / 环境变量示例
├── .gitignore
├── requirements.txt           # Project dependencies / 项目依赖
└── README.md
```

## Prerequisites / 先决条件

- Python 3.8+
- GitLab account with API access / 具有 API 访问权限的 GitLab 账户
- DeepSeek API access / DeepSeek API 访问权限
- Required Python packages (see requirements.txt) / 所需的 Python 包（见 requirements.txt）

## Installation / 安装

1. Clone the repository / 克隆仓库:
```bash
git clone https://github.com/yourusername/codereviewer.git
cd codereviewer
```

2. Create and activate a virtual environment / 创建并激活虚拟环境:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies / 安装依赖:
```bash
pip install -r requirements.txt
```

4. Copy the example environment file and configure your settings / 复制环境变量示例文件并配置设置:
```bash
cp .env.example .env
```

5. Edit `.env` with your configuration / 编辑 `.env` 配置:
```env
GITLAB_URL=https://your-gitlab-instance.com
GITLAB_TOKEN=your-gitlab-token
DEEPSEEK_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=your-deepseek-api-key
WEBHOOK_SECRET=your-webhook-secret
```

## Configuration / 配置

The system can be configured through environment variables or by modifying the settings in `src/codereviewer/config/settings.py`:

系统可以通过环境变量或修改 `src/codereviewer/config/settings.py` 中的设置进行配置：

- **GitLab Configuration / GitLab 配置**:
  - `GITLAB_URL`: Your GitLab instance URL / GitLab 实例 URL
  - `GITLAB_TOKEN`: Your GitLab API token / GitLab API 令牌

- **DeepSeek Configuration / DeepSeek 配置**:
  - `DEEPSEEK_URL`: DeepSeek API endpoint / DeepSeek API 端点
  - `DEEPSEEK_API_KEY`: Your DeepSeek API key / DeepSeek API 密钥

- **RAG Configuration / RAG 配置**:
  - `DOCUMENTS_FILE`: Path to your documents file / 文档文件路径
  - `EMBEDDING_DIMENSION`: Dimension of embeddings (default: 384) / 嵌入维度（默认：384）
  - `MAX_RETRIEVED_DOCS`: Maximum number of documents to retrieve (default: 2) / 最大检索文档数（默认：2）

- **Application Settings / 应用程序设置**:
  - `MAX_WORKERS`: Maximum number of concurrent workers / 最大并发工作线程数
  - `MAX_COMMENTS`: Maximum number of comments per review / 每次审查的最大评论数
  - `API_TIMEOUT`: API request timeout in seconds / API 请求超时时间（秒）
  - `RETRY_ATTEMPTS`: Number of retry attempts for failed requests / 失败请求的重试次数
  - `RETRY_DELAY`: Delay between retries in seconds / 重试间隔时间（秒）

## Usage / 使用方法

1. Start the application / 启动应用程序:
```bash
python src/codereviewer/app.py
```

2. Configure GitLab webhook / 配置 GitLab webhook:
   - Go to your GitLab project settings / 进入 GitLab 项目设置
   - Navigate to Webhooks / 导航到 Webhooks
   - Add a new webhook with the following settings / 添加具有以下设置的新 webhook:
     - URL: `http://your-server:5000/webhook`
     - Secret Token: Your configured `WEBHOOK_SECRET` / 密钥令牌：您配置的 `WEBHOOK_SECRET`
     - Trigger: Merge Request events / 触发器：合并请求事件

3. The system will automatically / 系统将自动:
   - Receive webhook notifications for merge requests / 接收合并请求的 webhook 通知
   - Analyze code changes using DeepSeek API / 使用 DeepSeek API 分析代码变更
   - Retrieve relevant documents using RAG / 使用 RAG 检索相关文档
   - Generate and post review comments / 生成并发布审查评论

## RAG Integration / RAG 集成

The system uses RAG to enhance code review by / 系统通过以下方式使用 RAG 增强代码审查:
1. Maintaining a knowledge base of code review best practices / 维护代码审查最佳实践的知识库
2. Retrieving relevant documents based on code changes / 基于代码变更检索相关文档
3. Using retrieved documents to provide context-aware suggestions / 使用检索到的文档提供上下文感知的建议

To add to the knowledge base / 添加到知识库:
1. Edit `documents.txt` with your code review guidelines / 使用代码审查指南编辑 `documents.txt`
2. Each line should contain a single document / 每行应包含一个文档
3. Documents should be concise and focused on specific best practices / 文档应简洁并专注于特定的最佳实践

## Error Handling / 错误处理

The system includes comprehensive error handling / 系统包含全面的错误处理:
- Automatic retry for failed API calls / API 调用失败时自动重试
- Detailed error logging / 详细的错误日志记录
- Graceful degradation when services are unavailable / 服务不可用时的优雅降级
- Webhook request validation / Webhook 请求验证

## Logging / 日志记录

Logs are stored in `reviewer.log` with the following format / 日志以以下格式存储在 `reviewer.log` 中:
```
[timestamp] [level] [message]
```

Log levels can be configured in settings / 日志级别可以在设置中配置:
- DEBUG: Detailed debugging information / 详细的调试信息
- INFO: General operational information / 一般操作信息
- WARNING: Warning messages / 警告消息
- ERROR: Error messages / 错误消息
- CRITICAL: Critical errors / 严重错误

## Contributing / 贡献

1. Fork the repository / 分叉仓库
2. Create a feature branch / 创建功能分支
3. Commit your changes / 提交更改
4. Push to the branch / 推送到分支
5. Create a Pull Request / 创建拉取请求

## License / 许可证

This project is licensed under the MIT License - see the LICENSE file for details.
本项目采用 MIT 许可证 - 详情请参阅 LICENSE 文件。

## Acknowledgments / 致谢

- [GitLab API](https://docs.gitlab.com/ee/api/)
- [DeepSeek API](https://deepseek.com/api)
- [Flask](https://flask.palletsprojects.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)