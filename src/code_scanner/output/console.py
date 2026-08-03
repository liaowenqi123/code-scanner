"""rich 彩色终端输出"""

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..quality import get_quality_level, SEVERITY_RICH
from . import SCANNER_TITLES


def render_report(results: dict) -> None:
    """打印彩色终端报告"""
    console = Console()
    score = results.get("quality_score")
    distribution = results.get("severity_distribution", {})
    level = get_quality_level(score) if score is not None else None

    # 汇总表格
    table = Table(title="扫描结果汇总", title_style="bold cyan", show_lines=False, pad_edge=False)
    table.add_column("扫描器", style="cyan")
    table.add_column("问题数", justify="right")

    total_issues = 0
    for scanner_name, scanner_data in results["scanners"].items():
        count = scanner_data["findings_count"]
        total_issues += count
        style = "green" if count == 0 else ("yellow" if count < 10 else "red")
        table.add_row(
            SCANNER_TITLES.get(scanner_name, scanner_name),
            Text(str(count), style=style),
        )

    # 评分面板
    if level is not None:
        bar_blocks = max(0, min(10, round(score / 10)))
        bar = "█" * bar_blocks + "░" * (10 - bar_blocks)
        score_text = Text()
        score_text.append(f"质量评分: ", style="bold")
        score_text.append(f"{score}/100", style=f"bold {level['rich_color']}")
        score_text.append(f"  {bar}", style=level["rich_color"])
        score_text.append(f"  {level['name']} ({level['desc']})", style=level["rich_color"])

        stats_text = Text()
        stats_text.append(f"扫描文件: {results['total_files']}   ", style="dim")
        stats_text.append(f"总问题: {total_issues}   ", style="bold")
        stats_text.append(f"high={distribution.get('high', 0)} ", style="red")
        stats_text.append(f"medium={distribution.get('medium', 0)} ", style="yellow")
        stats_text.append(f"low={distribution.get('low', 0)}", style="green")

        panel = Panel(
            Group(score_text, stats_text),
            title="Code Scanner Plus",
            border_style=level["rich_color"],
        )
        console.print(panel)

    console.print(table)


def print_findings(results: dict) -> None:
    """按文件打印详细问题（彩色）"""
    console = Console()
    from . import finding_parts

    # 按文件分组
    by_file = {}
    for scanner_data in results["scanners"].values():
        for finding in scanner_data.get("findings", []):
            by_file.setdefault(finding["file"], []).append(finding)

    if not by_file:
        console.print("[green]没有发现问题，代码很干净！[/green]")
        return

    for file_path, findings in sorted(by_file.items()):
        console.print(f"\n[bold magenta]{file_path}[/bold magenta]")
        for finding in findings:
            line, title, desc = finding_parts(finding)
            severity = finding.get("severity", "low")
            style = SEVERITY_RICH.get(severity, "white")
            text = Text()
            text.append(f"[{severity.upper()}]", style=style)
            text.append(f" L{line} ", style="bold")
            text.append(str(title), style="cyan")
            if desc:
                text.append(f" {desc}")
            console.print(f"  {text}")
