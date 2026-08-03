"""
CLI主入口 - 支持12个扫描器、严重级别与质量评分
"""

import json
import re
import click
from datetime import datetime
from pathlib import Path

from .scanners import (
    SecretScanner,
    FunctionLengthScanner,
    ImportScanner,
    TodoScanner,
    ComplexityScanner,
    LineLengthScanner,
    ErrorHandlingScanner,
    NamingScanner,
    MagicNumberScanner,
    DuplicateCodeScanner,
    StructureScanner,
    CommentsScanner,
)

# 严重级别权重（质量评分用）
SEVERITY_WEIGHTS = {"high": 5, "medium": 3, "low": 1}

# 旧扫描器的默认严重级别（旧 finding 无 severity 字段）
DEFAULT_SEVERITY = {
    "secret": "high",
    "function_length": "medium",
    "import": "low",
    "todo": "low",
}

# 扫描器中文标题（markdown 渲染用）
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

_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\u2600-\u27BF\U0000FE0F\U00002190-\U000021FF]+"
)


def _build_scanners() -> dict:
    """构建所有扫描器实例"""
    return {
        "secret": SecretScanner(),
        "function_length": FunctionLengthScanner(),
        "import": ImportScanner(),
        "todo": TodoScanner(),
        "complexity": ComplexityScanner(),
        "line_length": LineLengthScanner(),
        "error_handling": ErrorHandlingScanner(),
        "naming": NamingScanner(),
        "magic_number": MagicNumberScanner(),
        "duplicate": DuplicateCodeScanner(),
        "structure": StructureScanner(),
        "comments": CommentsScanner(),
    }


def _extract_findings(scanner_name: str, scanner_results: dict) -> list:
    """从扫描结果中提取问题列表，并补充默认严重级别"""
    findings = (
        scanner_results.get("all_findings")
        or scanner_results.get("all_functions")
        or scanner_results.get("all_unused_imports")
        or scanner_results.get("all_todos")
        or []
    )
    default_sev = DEFAULT_SEVERITY.get(scanner_name, "medium")
    normalized = []
    for finding in findings:
        item = dict(finding)
        item.setdefault("severity", default_sev)
        normalized.append(item)
    return normalized


def _compute_score(results: dict) -> tuple:
    """计算质量总分（0-100）和严重级别分布"""
    distribution = {"high": 0, "medium": 0, "low": 0}
    total_weight = 0
    for scanner_data in results["scanners"].values():
        for finding in scanner_data.get("findings", []):
            severity = finding.get("severity", "low")
            if severity not in distribution:
                severity = "low"
            distribution[severity] += 1
            total_weight += SEVERITY_WEIGHTS[severity]
    score = max(0, 100 - total_weight)
    return score, distribution


def _run_all_scanners(scanners: dict, path: str, results: dict) -> None:
    """运行所有扫描器并填充 results"""
    for name, scanner in scanners.items():
        click.echo(f"运行 {name} 扫描器...")
        scanner_results = scanner.scan_directory(path)
        findings = _extract_findings(name, scanner_results)

        results["total_files"] = max(
            results["total_files"], scanner_results.get("total_files", 0)
        )
        results["scanners"][name] = {
            "findings_count": len(findings),
            "findings": findings,
            "details": scanner_results,
        }


@click.group()
def main():
    """Code Scanner Plus - 代码审查辅助工具"""
    pass


@main.command()
@click.option('--path', '-p', default='.', help='扫描路径')
@click.option('--output', '-o', default='json', type=click.Choice(['json', 'markdown']))
@click.option('--file', '-f', default=None, help='输出到文件（markdown格式）')
def scan(path: str, output: str, file: str):
    """扫描代码问题"""
    path_obj = Path(path).resolve()

    if not path_obj.exists():
        click.echo(f"错误：路径不存在 {path}")
        return

    scanners = _build_scanners()
    results = {
        "scan_time": datetime.now().isoformat(),
        "path": str(path_obj),
        "total_files": 0,
        "scanners": {}
    }

    _run_all_scanners(scanners, str(path_obj), results)
    score, distribution = _compute_score(results)
    results["quality_score"] = score
    results["severity_distribution"] = distribution

    click.echo(f"\n扫描完成！")
    click.echo(f"扫描文件数: {results['total_files']}")

    for name, scanner_result in results["scanners"].items():
        click.echo(f"{name}: {scanner_result['findings_count']} 个问题")

    click.echo(f"\n质量评分: {score}/100")
    click.echo(
        "等级分布: high={high}, medium={medium}, low={low}".format(**distribution)
    )

    if output == 'json':
        click.echo("\n" + json.dumps(results, indent=2, ensure_ascii=False))
    elif output == 'markdown':
        markdown_content = _format_markdown(results)
        if file:
            output_path = Path(file)
            output_path.write_text(markdown_content, encoding='utf-8')
            click.echo(f"\n报告已保存到: {output_path}")
        else:
            # 输出到控制台（去除emoji避免编码问题）
            safe_content = _EMOJI_RE.sub('', markdown_content)
            click.echo("\n" + safe_content)


@main.command("self-report")
@click.argument('path')
def self_report(path: str):
    """生成self-report.json"""
    path_obj = Path(path).resolve()

    scanners = _build_scanners()
    results = {
        "scan_time": datetime.now().isoformat(),
        "path": str(path_obj),
        "scanner_name": "code-scanner-plus",
        "total_files": 0,
        "scanners": {},
        "summary": {}
    }

    _run_all_scanners(scanners, str(path_obj), results)
    score, distribution = _compute_score(results)
    results["quality_score"] = score
    results["severity_distribution"] = distribution

    results["summary"] = {
        "total_issues": sum(s["findings_count"] for s in results["scanners"].values()),
        "scanner_version": "2.0.0"
    }

    output_file = path_obj / "self-report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    click.echo(f"生成 self-report.json: {output_file}")
    click.echo(f"总问题数: {results['summary']['total_issues']}")
    click.echo(f"质量评分: {score}/100")


def _format_markdown(results: dict) -> str:
    """格式化输出为Markdown"""
    score = results.get("quality_score")
    distribution = results.get("severity_distribution", {})
    score_line = f"**质量评分**: {score}/100" if score is not None else ""

    lines = [
        "# Code Scanner Plus 报告",
        "",
        f"**扫描时间**: {results['scan_time']}",
        f"**扫描路径**: {results['path']}",
        f"**扫描文件数**: {results['total_files']}",
    ]
    if score_line:
        lines.append(score_line)
        lines.append(
            f"**等级分布**: high={distribution.get('high', 0)}, "
            f"medium={distribution.get('medium', 0)}, low={distribution.get('low', 0)}"
        )
    lines += ["", "## 扫描结果汇总", ""]

    for scanner_name, scanner_data in results['scanners'].items():
        title = SCANNER_TITLES.get(scanner_name, scanner_name)
        count = scanner_data['findings_count']
        lines.append(f"- **{title}** ({scanner_name}): {count} 个问题")

    lines.append("")
    lines.append("## 详细问题列表")
    lines.append("")

    # 旧扫描器：保留专门渲染
    _render_secret(lines, results)
    _render_function_length(lines, results)
    _render_imports(lines, results)
    _render_todo(lines, results)

    # 新扫描器：通用渲染
    generic_scanners = [
        "complexity", "line_length", "error_handling", "naming",
        "magic_number", "duplicate", "structure", "comments",
    ]
    for name in generic_scanners:
        data = results['scanners'].get(name)
        if data and data['findings_count'] > 0:
            _render_generic(lines, SCANNER_TITLES[name], data['findings'])

    return "\n".join(lines)


def _render_generic(lines: list, title: str, findings: list) -> None:
    """通用渲染新扫描器的问题列表"""
    sev_badge = {"high": "🔴", "medium": "🟡", "low": "🟢"}
    lines.append(f"### {title}")
    lines.append("")
    for finding in findings:
        badge = sev_badge.get(finding.get("severity", "low"), "⚪")
        lines.append(f"- **{finding.get('type', '问题')}** {badge} {finding.get('message', '')}")
        lines.append(f"  - **文件**: {finding['file']}")
        lines.append(f"  - **行号**: {finding.get('line', '-')}")
        lines.append("")


def _render_secret(lines: list, results: dict) -> None:
    data = results['scanners'].get('secret')
    if not data or data['findings_count'] == 0:
        return
    lines.append("### 🔐 敏感信息")
    lines.append("")
    for finding in data['findings']:
        lines.append(f"- **文件**: {finding['file']}")
        lines.append(f"  - **类型**: {finding['type']}")
        lines.append(f"  - **行号**: {finding['line']}")
        lines.append(f"  - **匹配**: `{finding['match']}`")
        lines.append("")


def _render_function_length(lines: list, results: dict) -> None:
    data = results['scanners'].get('function_length')
    if not data or data['findings_count'] == 0:
        return
    lines.append("### 📏 超长函数")
    lines.append("")
    for finding in data['findings']:
        lines.append(f"- **函数**: `{finding['function_name']}`")
        lines.append(f"  - **文件**: {finding['file']}")
        lines.append(f"  - **行数**: {finding['line_count']} (行 {finding['start_line']}-{finding['end_line']})")
        lines.append("")


def _render_imports(lines: list, results: dict) -> None:
    data = results['scanners'].get('import')
    if not data or data['findings_count'] == 0:
        return
    lines.append("### 📦 未使用导入")
    lines.append("")
    for finding in data['findings']:
        lines.append(f"- **导入**: `{finding['import_statement']}`")
        lines.append(f"  - **文件**: {finding['file']}")
        lines.append(f"  - **行号**: {finding['line_number']}")
        lines.append("")


def _render_todo(lines: list, results: dict) -> None:
    data = results['scanners'].get('todo')
    if not data or data['findings_count'] == 0:
        return
    lines.append("### ✅ TODO/FIXME")
    lines.append("")
    for finding in data['findings']:
        age_status = "⚠️ 超过7天" if finding.get('over_7_days') else "✨ 新建"
        lines.append(f"- **内容**: `{finding['content']}`")
        lines.append(f"  - **文件**: {finding['file']}")
        lines.append(f"  - **行号**: {finding['line']}")
        lines.append(f"  - **状态**: {age_status}")
        lines.append("")


if __name__ == '__main__':
    main()
