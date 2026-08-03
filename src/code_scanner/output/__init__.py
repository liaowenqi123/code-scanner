"""输出渲染模块：彩色终端 / Markdown / HTML"""

# 扫描器中文标题
SCANNER_TITLES = {
    "secret": "敏感信息",
    "function_length": "超长函数",
    "import": "未使用导入",
    "todo": "TODO/FIXME",
    "complexity": "圈复杂度 / 嵌套深度",
    "line_length": "超长行",
    "error_handling": "错误处理",
    "naming": "命名规范",
    "magic_number": "魔法数字",
    "duplicate": "重复代码",
    "structure": "结构问题",
    "comments": "注释质量",
}


def finding_parts(finding: dict) -> tuple:
    """将不同扫描器的 finding 统一为 (行号, 标题, 描述) 三元组"""
    line = (
        finding.get("line")
        or finding.get("line_number")
        or finding.get("start_line")
        or "-"
    )

    # 标题：优先使用子类型/函数名/导入语句等
    title = (
        finding.get("type")
        or finding.get("function_name")
        or finding.get("import_name")
        or finding.get("name")
    )
    if title is None:
        title = "问题"

    # 描述：优先使用 message，否则从各扫描器字段拼装
    desc = finding.get("message")
    if not desc:
        if "import_statement" in finding:
            desc = finding["import_statement"]
        elif "line_count" in finding:
            desc = f"{finding['line_count']} 行 (行 {finding['start_line']}-{finding['end_line']})"
        elif "match" in finding:
            desc = f"{finding.get('type', '')} {finding['match']}".strip()
        elif "content" in finding:
            age = "超过7天" if finding.get("over_7_days") else "新建"
            desc = f"状态: {age}"
        else:
            desc = ""

    return line, title, desc
