# Logging 改进说明

## 概述
本次修改增强了代码审查应用的logging功能，使其能够在日志输出中显示从LLM（大语言模型）返回的comment内容。

## 修改内容

### 1. 核心审查器 (`src/codereviewer/core/reviewer.py`)

#### 在 `_generate_comments` 方法中：
- 添加了LLM原始分析结果的logging输出
- 记录每个文件的LLM分析结果

```python
# 记录LLM返回的原始分析结果
logger.info(f"LLM analysis for {diff.new_path}: {analysis}")
```

#### 在 `_parse_comments` 方法中：
- 添加了解析出的评论内容的logging输出
- 记录每个解析出的评论的详细信息

```python
# 记录解析出的评论内容
logger.info(f"Parsed comment for {file_path} line {line_num} ({line_type}): {comment_text}")
```

#### 在 `_post_comments` 方法中：
- 增强了发布评论时的logging输出
- 包含评论的具体内容

```python
logger.info(f"Posted comment on line {comment.line} of {comment.file_path}: {comment.comment}")
```

#### 在 `_generate_summary` 方法中：
- 添加了摘要生成结果的logging输出

```python
logger.info(f"Summary generation completed: {summary}")
```

### 2. DeepSeek API客户端 (`src/codereviewer/api/deepseek.py`)

#### 在 `analyze_code_diff` 方法中：
- 添加了API请求和响应的logging输出
- 记录发送请求和接收响应的过程

```python
logger.info(f"Sending code review request to DeepSeek API for diff analysis")
logger.info(f"Received LLM response for code review: {content}")
```

#### 在 `generate_review_summary` 方法中：
- 添加了摘要生成请求和响应的logging输出

```python
logger.info(f"Sending summary generation request to DeepSeek API")
logger.info(f"Received LLM response for summary generation: {content}")
```

## 日志输出示例

### LLM分析结果日志：
```
2024-01-01 12:00:00 - codereviewer.core.reviewer - INFO - LLM analysis for src/main.py: 行 10 类型 +: 建议添加类型注解以提高代码可读性
行 15 类型 +: 考虑添加异常处理机制
```

### 解析评论日志：
```
2024-01-01 12:00:01 - codereviewer.core.reviewer - INFO - Parsed comment for src/main.py line 10 (+): 建议添加类型注解以提高代码可读性
2024-01-01 12:00:01 - codereviewer.core.reviewer - INFO - Parsed comment for src/main.py line 15 (+): 考虑添加异常处理机制
```

### 发布评论日志：
```
2024-01-01 12:00:02 - codereviewer.core.reviewer - INFO - Posted comment on line 10 of src/main.py: 建议添加类型注解以提高代码可读性
```

### API请求日志：
```
2024-01-01 12:00:00 - codereviewer.api.deepseek - INFO - Sending code review request to DeepSeek API for diff analysis
2024-01-01 12:00:01 - codereviewer.api.deepseek - INFO - Received LLM response for code review: 行 10 类型 +: 建议添加类型注解以提高代码可读性
```

## 测试

运行测试脚本验证修改：
```bash
python test_logging.py
```

## 配置

logging配置在 `src/codereviewer/utils/logger.py` 中，支持：
- 控制台输出
- 文件输出（轮转日志）
- 可配置的日志级别
- 自定义格式化器

## 注意事项

1. 确保在生产环境中适当配置日志级别，避免敏感信息泄露
2. 日志文件可能会变得较大，建议定期清理
3. 如果LLM返回的内容很长，日志输出也会相应较长
