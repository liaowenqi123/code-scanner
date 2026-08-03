"""HTML 可视化报告渲染：深色主题，浏览器打开即用"""

import html
from typing import Dict, List

from ..quality import get_quality_level
from . import SCANNER_TITLES, finding_parts

_SEVERITY_CLASS = {"high": "high", "medium": "medium", "low": "low"}
_SEVERITY_LABEL = {"high": "高", "medium": "中", "low": "低"}

_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
       background: #0d1117; color: #c9d1d9; line-height: 1.6; padding: 2rem; }
.container { max-width: 960px; margin: 0 auto; }
h1 { text-align: center; font-size: 1.8rem; margin-bottom: 0.4rem; color: #f0c674; }
h2 { color: #bd93f9; margin: 1.5rem 0 0.8rem; font-size: 1.3rem;
     border-bottom: 1px solid #21262d; padding-bottom: 0.5rem; }
.meta { text-align: center; color: #8b949e; font-size: 0.9rem; margin-bottom: 1.5rem; }
.score-card { background: #161b22; border: 1px solid #30363d; border-radius: 12px;
              padding: 2rem; text-align: center; margin-bottom: 1.5rem; }
.score-value { font-size: 4rem; font-weight: bold; line-height: 1.1; }
.score-level { font-size: 1.4rem; margin-top: 0.6rem; font-weight: 600; }
.score-desc { color: #8b949e; margin-top: 0.3rem; font-size: 0.95rem; }
.stats { display: flex; gap: 0.8rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.stat-card { flex: 1; min-width: 120px; background: #161b22; border: 1px solid #30363d;
             border-radius: 8px; padding: 1rem; text-align: center; }
.stat-value { font-size: 1.6rem; font-weight: bold; }
.stat-label { font-size: 0.8rem; color: #8b949e; }
table { width: 100%; border-collapse: collapse; margin: 0.5rem 0 1.5rem; }
th { background: #161b22; color: #bd93f9; text-align: left; padding: 0.7rem;
     border-bottom: 2px solid #30363d; }
td { padding: 0.7rem; border-bottom: 1px solid #21262d; font-size: 0.9rem; word-break: break-all; }
tr:hover td { background: #161b22; }
.file-card { background: #161b22; border: 1px solid #30363d; border-radius: 8px;
             padding: 1.1rem 1.25rem; margin-bottom: 1rem; }
.file-path { color: #d2a8ff; font-weight: 600; font-family: Consolas, 'Courier New', monospace;
             font-size: 0.82rem; word-break: break-all; }
.file-count { float: right; color: #8b949e; font-size: 0.8rem; }
details.issues { margin-top: 0.4rem; }
details.issues summary { cursor: pointer; color: #8b949e; font-size: 0.82rem;
                         padding: 0.25rem 0; user-select: none; list-style: none; }
details.issues summary::before { content: "▸ "; font-size: 0.75rem; }
details.issues[open] summary::before { content: "▾ "; }
details.issues summary:hover { color: #58a6ff; }
details.issues .issue-list { margin-top: 0.3rem; }
.issue { padding: 0.45rem 0; border-bottom: 1px dashed #21262d; font-size: 0.9rem; }
.issue:last-child { border-bottom: none; }
.issue-line { display: inline-block; min-width: 3.5rem; color: #58a6ff;
              font-family: Consolas, monospace; font-size: 0.82rem; }
.badge { display: inline-block; min-width: 2.2rem; text-align: center; padding: 0.1rem 0.5rem;
         border-radius: 10px; font-size: 0.72rem; font-weight: 700; margin-right: 0.5rem; }
.badge.high { background: rgba(248,81,73,0.18); color: #f85149; }
.badge.medium { background: rgba(210,153,34,0.18); color: #d29922; }
.badge.low { background: rgba(63,185,80,0.18); color: #3fb950; }
.issue-type { color: #79c0ff; font-family: Consolas, monospace; font-size: 0.82rem; margin-right: 0.5rem; }
.issue-desc { color: #c9d1d9; }
.empty { color: #8b949e; text-align: center; padding: 1rem; }
.footer { text-align: center; margin-top: 2rem; color: #484f58; font-size: 0.8rem;
          border-top: 1px solid #21262d; padding-top: 1rem; }
"""


def _stat_cards(results: dict, total_issues: int, distribution: dict) -> str:
    cards = [
        ("扫描文件", str(results["total_files"]), "#58a6ff"),
        ("总问题数", str(total_issues), "#c9d1d9"),
        ("高危", str(distribution.get("high", 0)), "#f85149"),
        ("中危", str(distribution.get("medium", 0)), "#d29922"),
        ("低危", str(distribution.get("low", 0)), "#3fb950"),
    ]
    return "".join(
        f'<div class="stat-card"><div class="stat-value" style="color:{color}">{value}</div>'
        f'<div class="stat-label">{label}</div></div>'
        for label, value, color in cards
    )


def _summary_table(results: dict) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(SCANNER_TITLES.get(name, name))}</td>"
        f"<td>{data['findings_count']}</td></tr>"
        for name, data in results["scanners"].items()
    )
    return (
        "<table><thead><tr><th>扫描器</th><th>问题数</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def _issue_html(finding: dict) -> str:
    line, title, desc = finding_parts(finding)
    severity = finding.get("severity", "low")
    cls = _SEVERITY_CLASS.get(severity, "low")
    label = _SEVERITY_LABEL.get(severity, "-")
    return (
        f'<div class="issue"><span class="issue-line">L{html.escape(str(line))}</span>'
        f'<span class="badge {cls}">{label}</span>'
        f'<span class="issue-type">{html.escape(str(title))}</span>'
        f'<span class="issue-desc">{html.escape(str(desc))}</span></div>'
    )


def _file_sections(results: dict) -> str:
    by_file: Dict[str, List[dict]] = {}
    for scanner_data in results["scanners"].values():
        for finding in scanner_data.get("findings", []):
            by_file.setdefault(finding["file"], []).append(finding)

    if not by_file:
        return '<div class="empty">没有发现问题，代码很干净！</div>'

    sections = []
    for file_path in sorted(by_file):
        findings = by_file[file_path]
        issues = "".join(_issue_html(f) for f in findings)
        sections.append(
            f'<div class="file-card"><div class="file-count">{len(findings)} 个问题</div>'
            f'<div class="file-path">{html.escape(file_path)}</div>'
            f'<details class="issues"><summary>查看问题明细</summary>'
            f'<div class="issue-list">{issues}</div></details></div>'
        )
    return "\n".join(sections)


def render_html(results: dict) -> str:
    """渲染 HTML 报告"""
    score = results.get("quality_score")
    distribution = results.get("severity_distribution", {})
    level = get_quality_level(score) if score is not None else None

    total_issues = sum(s["findings_count"] for s in results["scanners"].values())

    if level:
        score_block = (
            f'<div class="score-value" style="color:{level["html_color"]}">{score}/100</div>'
            f'<div class="score-level">{level["emoji"]} {level["name"]}</div>'
            f'<div class="score-desc">{level["desc"]}</div>'
        )
    else:
        score_block = '<div class="score-value">-</div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Code Scanner Plus 报告</title>
<style>{_CSS}</style>
</head>
<body>
<div class="container">
  <h1>Code Scanner Plus 报告</h1>
  <div class="meta">扫描时间: {html.escape(results['scan_time'])} &nbsp;|&nbsp; 扫描路径: {html.escape(results['path'])}</div>

  <div class="score-card">{score_block}</div>
  <div class="stats">{_stat_cards(results, total_issues, distribution)}</div>

  <h2>扫描器汇总</h2>
  {_summary_table(results)}

  <h2>详细问题</h2>
  {_file_sections(results)}

  <div class="footer">Generated by code-scanner-plus | 离线静态分析，代码不会离开你的机器</div>
</div>
</body>
</html>
"""
