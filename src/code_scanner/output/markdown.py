"""Markdown 报告渲染：汇总与详情均使用表格"""

from ..quality import get_quality_level
from . import SCANNER_TITLES, finding_parts

_SEVERITY_LABEL = {"high": "高", "medium": "中", "low": "低"}


def render_markdown(results: dict) -> str:
    """渲染 Markdown 报告"""
    score = results.get("quality_score")
    distribution = results.get("severity_distribution", {})
    level = get_quality_level(score) if score is not None else None

    lines = [
        "# Code Scanner Plus 报告",
        "",
        "## 概览",
        "",
        "| 项目 | 值 |",
        "| --- | --- |",
        f"| 扫描时间 | {results['scan_time']} |",
        f"| 扫描路径 | `{results['path']}` |",
        f"| 扫描文件数 | {results['total_files']} |",
    ]
    if level:
        lines.append(f"| 质量评分 | **{score}/100** {level['emoji']} {level['name']} |")
        lines.append(
            f"| 等级分布 | high={distribution.get('high', 0)} / "
            f"medium={distribution.get('medium', 0)} / low={distribution.get('low', 0)} |"
        )

    lines += [
        "",
        "## 扫描器汇总",
        "",
        "| 扫描器 | 问题数 |",
        "| --- | --- |",
    ]
    for scanner_name, scanner_data in results["scanners"].items():
        title = SCANNER_TITLES.get(scanner_name, scanner_name)
        lines.append(f"| {title} | {scanner_data['findings_count']} |")

    lines += ["", "## 详细问题", ""]

    for scanner_name, scanner_data in results["scanners"].items():
        if scanner_data["findings_count"] == 0:
            continue
        title = SCANNER_TITLES.get(scanner_name, scanner_name)
        lines.append(f"### {title}")
        lines.append("")
        lines.append("| 级别 | 行号 | 类型 | 描述 |")
        lines.append("| --- | --- | --- | --- |")
        for finding in scanner_data["findings"]:
            line, finding_title, desc = finding_parts(finding)
            severity = _SEVERITY_LABEL.get(finding.get("severity", "low"), "-")
            lines.append(
                f"| {severity} | {line} | `{finding_title}` | {desc} |"
            )
        lines.append("")

    return "\n".join(lines)
