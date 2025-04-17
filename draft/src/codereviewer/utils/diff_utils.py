import re
from typing import List, Dict, Any

def add_new_file_line_numbers(diff_str: str) -> str:
    """
    为 Git diff 中的每一行附上其在对应文件中的行号。
    - 对于上下文行和 +行，使用新文件中的行号。
    - 对于 -行，使用旧文件中的行号。
    - 对于 hunk header 行，标记为 "N/A"。
    """
    lines = diff_str.splitlines()
    result_lines = []
    current_old_line = None
    current_new_line = None
    in_hunk = False

    for line in lines:
        hunk_match = re.match(r'@@ -(\d+),\d+ \+(\d+),\d+ @@', line)
        if hunk_match:
            current_old_line = int(hunk_match.group(1))
            current_new_line = int(hunk_match.group(2))
            in_hunk = True
            result_lines.append(f"N/A: {line}")
            continue
        if not in_hunk:
            result_lines.append(f"N/A: {line}")
            continue
        if line.startswith('-'):
            result_lines.append(f"{current_old_line}: {line}")
            current_old_line += 1
        elif line.startswith('+'):
            result_lines.append(f"{current_new_line}: {line}")
            current_new_line += 1
        else:
            result_lines.append(f"{current_new_line}: {line}")
            current_old_line += 1
            current_new_line += 1
    return "\n".join(result_lines)

def parse_comment(comment: str) -> Dict[str, Any]:
    """
    解析评论字符串，提取行号、类型和评论内容
    格式：行 X 类型 Y: 建议（30 字以内）, 原始代码
    """
    match = re.search(r'行\s*(\d+)\s*类型\s*([+-])\s*:\s*(.*)', comment)
    if match:
        line, line_type, comment_text = match.groups()
        return {
            "line": int(line),
            "line_type": line_type,
            "comment": comment_text
        }
    return None

def format_diff_for_analysis(diff: List[Dict[str, Any]]) -> str:
    """
    格式化diff数据用于分析
    """
    formatted_diffs = []
    for file_diff in diff:
        new_file_path = file_diff.get('new_path', '')
        diff_content = file_diff.get('diff', '')
        formatted_diff = add_new_file_line_numbers(diff_content)
        formatted_diffs.append(f"File: {new_file_path}\n{formatted_diff}")
    return "\n\n".join(formatted_diffs) 