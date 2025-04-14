# Automated Code Review System

An intelligent code review system that integrates with GitLab and leverages the DeepSeek API for automated code analysis and review suggestions.

## Features

- **Automated Code Review**: Automatically analyzes merge requests and provides review comments
- **AI-Powered Analysis**: Utilizes DeepSeek API for intelligent code analysis
- **RAG Integration**: Enhances code review with relevant documentation context
- **Asynchronous Processing**: Handles multiple review requests efficiently
- **Configurable Settings**: Flexible configuration through environment variables
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Secure Webhook Handling**: Validates GitLab webhook requests
- **Retry Mechanism**: Handles API failures gracefully
- **Caching System**: Optimizes performance with diff caching

## Project Structure

```
codereviewer/
│
├── src/
│   └── codereviewer/
│       ├── api/
│       │   ├── deepseek.py     # DeepSeek API integration
│       │   └── gitlab.py       # GitLab API integration
│       │
│       ├── config/
│       │   └── settings.py     # Configuration settings
│       │
│       ├── core/
│       │   └── reviewer.py     # Core review logic
│       │
│       ├── models/
│       │   └── rag.py         # RAG data models
│       │
│       ├── utils/
│       │   ├── logger.py      # Logging utilities
│       │   ├── diff_utils.py  # Diff processing utilities
│       │   └── rag_utils.py   # RAG utilities
│       │
│       └── app.py            # Main application
│
├── docs/                     # Documentation
├── requirements.txt         # Project dependencies
└── README.md              # Project documentation
```

## Prerequisites

- Python 3.8+
- GitLab account with API access
- DeepSeek API access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/codereviewer.git
cd codereviewer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

## Configuration

Configure the following settings in your `.env` file:

```ini
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your_gitlab_token
DEEPSEEK_URL=https://api.deepseek.com
DEEPSEEK_API_KEY=your_deepseek_api_key
WEBHOOK_SECRET=your_webhook_secret
```

Additional settings can be configured in `src/codereviewer/config/settings.py`.

## Usage

1. Start the application:
```bash
python src/codereviewer/app.py
```

2. Configure GitLab webhook:
   - Go to your GitLab project settings
   - Add a webhook for merge request events
   - Set the URL to your application's webhook endpoint
   - Add the webhook secret

## RAG Integration

The system uses Retrieval-Augmented Generation (RAG) to enhance code reviews by:
- Indexing project documentation and coding standards
- Retrieving relevant context during code review
- Providing more informed and context-aware suggestions

## Error Handling

The system includes comprehensive error handling:
- API request retries with exponential backoff
- Detailed error logging
- Graceful failure handling
- Cache-based recovery mechanisms

## Logging

Logs are stored in `reviewer.log` with the following format:
```
[TIMESTAMP] [LEVEL] [MODULE] Message
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 