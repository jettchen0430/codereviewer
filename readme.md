# 自动代码审查系统

这是一个基于 Flask 的自动代码审查系统，通过 GitLab Webhook 监听 Merge Request 事件，自动分析代码 diff，并使用 DeepSeek API 生成审查评论。系统集成了 RAG（Retrieval-Augmented Generation）技术，通过文档库增强评论的准确性和相关性。

## 功能特点

- **Webhook 集成**：监听 GitLab Merge Request 事件，自动触发代码审查。
- **异步处理**：使用线程池异步处理审查任务，提高并发性能。
- **日志记录**：同时记录到文件和终端，便于调试和监控。
- **缓存机制**：缓存 diff 内容，支持重试机制。
- **容错处理**：API 调用失败时自动重试，解析失败时提供默认评论。
- **RAG 技术**：通过文档库检索相关信息，提升评论质量。

## 安装和配置

### 1. 安装依赖

安装所需的 Python 库：
```bash
pip install flask requests tenacity faiss-cpu numpy
```
### 2. 配置环境变量
在项目根目录下创建 .env 文件，配置以下环境变量：


GITLAB_URL=https://gitlab.com/api/v4
GITLAB_TOKEN=your_gitlab_token
DEEPSEEK_URL=https://api.deepseek.com/v1
DEEPSEEK_API_KEY=your_deepseek_api_key
WEBHOOK_SECRET=your_webhook_secret
- **GITLAB_URL:** *GitLab API 的基础 URL*
- **GITLAB_TOKEN:** *GitLab 个人访问令牌，用于 API 认证*
- **DEEPSEEK_URL:** *DeepSeek API 的基础 URL*
- **DEEPSEEK_API_KEY:** *DeepSeek API 的密钥*
- **WEBHOOK_SECRET:** *Webhook 的密钥，用于验证请求来源*
### 3. 准备文档库
在项目根目录下创建 documents.txt 文件，每行一条代码审查建议，例如：
Always use descriptive variable names.
Avoid magic numbers in code.
这些建议将被 RAG 技术用于增强评论生成。

## 使用方法
1. 启动 Flask 应用
在项目根目录下运行：
```bash
python app_v2.py
```
应用将在 http://localhost:8000/webhook 监听 Webhook 请求。

2. 配置 GitLab Webhook
在 GitLab 项目中添加 Webhook：

- URL：http://your-server:8000/webhook
- Secret Token：与 .env 中的WEBHOOK_SECRET 一致
- 触发事件：勾选 “Merge Request events”
3. 代码审查流程
    1. GitLab 触发 Merge Request 事件。
    2.  Flask 应用接收 Webhook 请求，异步触发代码审查。
    3. 获取 Merge Request 详情和 diff 数据。
    4. 使用 RAG 技术检索相关文档。
    5. 调用 DeepSeek API 分析 diff 并生成评论（每条评论附带行号和建议）。
    6. 将评论提交到 GitLab 的提交上。
## 代码结构
- app.py：主应用文件，包含 Flask 路由、Webhook 处理、代码审查逻辑等。
- rag.py：实现 RAG 技术的检索功能（需自行实现 embeddings 和检索逻辑）。
- documents.txt：存储代码审查建议的文档库。
- reviewer.log：日志文件，记录运行时信息。
### 主要函数
- handle_webhook()：处理 Webhook 请求，验证来源并触发审查。
- trigger_review()：协调审查流程，调用 API 并提交评论。
- analyze_code_with_llm()：使用 DeepSeek API 分析 diff，生成评论。
- add_new_file_line_numbers()：为 diff 添加行号，便于定位问题。
- submit_comments_to_commit()：将评论提交到 GitLab。
## 注意事项
- 安全性：确保环境变量（如 API 密钥）存储在 .env 文件中，避免泄露。
- 性能：对于大 diff 文件，系统会自动缓存并分块处理，避免内存溢出。
- 容错：API 调用失败时，系统会自动重试 3 次，每次间隔 2 秒。若仍失败，将生成默认评论。
## 贡献和许可
欢迎贡献者参与项目！请提交 Pull Request 或报告 Issue。

本项目采用 MIT License，详情见  文件。