# 自动代码审查系统

一个智能代码审查系统，集成了 GitLab 并利用 DeepSeek API 进行自动代码分析和审查建议。

## 功能特点

- **自动代码审查**：自动分析合并请求并提供审查意见
- **AI 驱动分析**：利用 DeepSeek API 进行智能代码分析
- **RAG 集成**：通过相关文档上下文增强代码审查
- **异步处理**：高效处理多个审查请求
- **可配置设置**：通过环境变量进行灵活配置
- **全面日志记录**：详细的监控和调试日志
- **安全的 Webhook 处理**：验证 GitLab webhook 请求
- **重试机制**：优雅处理 API 失败
- **缓存系统**：通过 diff 缓存优化性能

## 项目结构

```
codereviewer/
│
├── src/
│   └── codereviewer/
│       ├── api/
│       │   ├── deepseek.py     # DeepSeek API 集成
│       │   └── gitlab.py       # GitLab API 集成
│       │
│       ├── config/
│       │   └── settings.py     # 配置设置
│       │
│       ├── core/
│       │   └── reviewer.py     # 核心审查逻辑
│       │
│       ├── models/
│       │   └── rag.py         # RAG 数据模型
│       │
│       ├── utils/
│       │   ├── logger.py      # 日志工具
│       │   ├── diff_utils.py  # Diff 处理工具
│       │   └── rag_utils.py   # RAG 工具
│       │
│       └── app.py            # 主应用程序
│
├── docs/                     # 文档
├── requirements.txt         # 项目依赖
└── README.md              # 项目文档
```

## 前置条件

- Python 3.8+
- GitLab 账号和 API 访问权限
- DeepSeek API 访问权限

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/codereviewer.git
cd codereviewer
```

2. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件设置你的配置
```

## 配置

在 `.env` 文件中配置以下设置：

```ini
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your_gitlab_token
DEEPSEEK_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=your_deepseek_api_key
WEBHOOK_SECRET=your_webhook_secret
```

其他设置可以在 `src/codereviewer/config/settings.py` 中配置。

## 使用方法

1. 启动应用：
```bash
python src/codereviewer/app.py
```

2. 配置 GitLab webhook：
   - 进入 GitLab 项目设置
   - 添加合并请求事件的 webhook
   - 设置应用的 webhook 端点 URL
   - 添加 webhook 密钥

## RAG 集成

系统使用检索增强生成（RAG）来增强代码审查：
- 索引项目文档和编码标准
- 在代码审查期间检索相关上下文
- 提供更有见地和上下文感知的建议

## 错误处理

系统包含全面的错误处理：
- 带指数退避的 API 请求重试
- 详细的错误日志记录
- 优雅的失败处理
- 基于缓存的恢复机制

## 日志记录

日志存储在 `reviewer.log` 中，格式如下：
```
[时间戳] [级别] [模块] 消息
```

## 贡献

1. Fork 仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 LICENSE 文件 