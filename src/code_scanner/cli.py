"""
CLI主入口 - 支持12个扫描器、severity分级、质量评分与四种输出格式
"""

import json
import click
from datetime import datetime
from pathlib import Path

from rich.console import Console

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
from .output.console import render_report, print_findings
from .output.markdown import render_markdown
from .output.html import render_html

# 严重级别权重（质量评分用）
SEVERITY_WEIGHTS = {"high": 5, "medium": 3, "low": 1}

# 旧扫描器的默认严重级别（旧 finding 无 severity 字段）
DEFAULT_SEVERITY = {
    "secret": "high",
    "function_length": "medium",
    "import": "low",
    "todo": "low",
}

console = Console()


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
        console.print(f"[dim]运行[/dim] [bold cyan]{name}[/bold cyan] 扫描器...")
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
@click.option('--output', '-o', default='console',
              type=click.Choice(['console', 'json', 'markdown', 'html']))
@click.option('--file', '-f', default=None, help='输出到文件（markdown/html格式）')
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

    console.print(f"\n[bold green]扫描完成！[/bold green] 共 {results['total_files']} 个文件")

    if output == 'json':
        console.print(json.dumps(results, indent=2, ensure_ascii=False))
    elif output == 'markdown':
        markdown_content = render_markdown(results)
        if file:
            Path(file).write_text(markdown_content, encoding='utf-8')
            console.print(f"[green]报告已保存到:[/green] {file}")
        else:
            console.print(markdown_content)
    elif output == 'html':
        html_content = render_html(results)
        if file:
            Path(file).write_text(html_content, encoding='utf-8')
            console.print(f"[green]HTML报告已保存到:[/green] {file}")
        else:
            console.print("[yellow]HTML 报告请使用 --file 参数保存后浏览器打开[/yellow]")
    else:
        # console（默认）：评分面板 + 汇总表 + 详细问题
        render_report(results)
        print_findings(results)


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

    render_report(results)
    console.print(f"\n[green]生成 self-report.json:[/green] {output_file}")


if __name__ == '__main__':
    main()
