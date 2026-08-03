"""
CLI主入口 - 修复版
"""

import json
import click
from datetime import datetime
from pathlib import Path

from .scanners import SecretScanner, FunctionLengthScanner, ImportScanner, TodoScanner


@click.group()
def main():
    """Code Scanner - 代码审查辅助工具"""
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

    scanners = {
        "secret": SecretScanner(),
        "function_length": FunctionLengthScanner(),
        "import": ImportScanner(),
        "todo": TodoScanner()
    }

    results = {
        "scan_time": datetime.now().isoformat(),
        "path": str(path_obj),
        "total_files": 0,
        "scanners": {}
    }

    for name, scanner in scanners.items():
        click.echo(f"运行 {name} 扫描器...")
        scanner_results = scanner.scan_directory(str(path_obj))

        findings = (
            scanner_results.get("all_findings") or
            scanner_results.get("all_functions") or
            scanner_results.get("all_unused_imports") or
            scanner_results.get("all_todos") or
            []
        )

        results["total_files"] = max(results["total_files"], scanner_results.get("total_files", 0))
        results["scanners"][name] = {
            "findings_count": len(findings),
            "details": scanner_results
        }

    click.echo(f"\n扫描完成！")
    click.echo(f"扫描文件数: {results['total_files']}")

    for name, scanner_result in results["scanners"].items():
        click.echo(f"{name}: {scanner_result['findings_count']} 个问题")

    if output == 'json':
        click.echo("\n" + json.dumps(results, indent=2, ensure_ascii=False))
    elif output == 'markdown':
        markdown_content = _format_markdown(results)
        if file:
            # 保存到文件
            output_path = Path(file)
            output_path.write_text(markdown_content, encoding='utf-8')
            click.echo(f"\n报告已保存到: {output_path}")
        else:
            # 输出到控制台（去除emoji避免编码问题）
            safe_content = markdown_content.replace('🔐', '[SEC]').replace('📏', '[LEN]').replace('📦', '[IMP]').replace('✅', '[TODO]').replace('⚠️', '[WARN]').replace('✨', '[NEW]')
            click.echo("\n" + safe_content)


@main.command("self-report")
@click.argument('path')
def self_report(path: str):
    """生成self-report.json"""
    path_obj = Path(path).resolve()

    scanners = {
        "secret": SecretScanner(),
        "function_length": FunctionLengthScanner(),
        "import": ImportScanner(),
        "todo": TodoScanner()
    }

    results = {
        "scan_time": datetime.now().isoformat(),
        "path": str(path_obj),
        "scanner_name": "code-scanner",
        "total_files": 0,
        "scanners": {},
        "summary": {}
    }

    for name, scanner in scanners.items():
        scanner_results = scanner.scan_directory(str(path_obj))
        findings = (
            scanner_results.get("all_findings") or
            scanner_results.get("all_functions") or
            scanner_results.get("all_unused_imports") or
            scanner_results.get("all_todos") or
            []
        )

        results["total_files"] = max(results["total_files"], scanner_results.get("total_files", 0))
        results["scanners"][name] = {
            "findings_count": len(findings),
            "findings": findings
        }

    results["summary"] = {
        "total_issues": sum(s["findings_count"] for s in results["scanners"].values()),
        "scanner_version": "1.0.0"
    }

    output_file = path_obj / "self-report.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    click.echo(f"生成 self-report.json: {output_file}")
    click.echo(f"总问题数: {results['summary']['total_issues']}")


def _format_markdown(results: dict) -> str:
    """格式化输出为Markdown"""
    lines = [
        "# Code Scanner 报告",
        "",
        f"**扫描时间**: {results['scan_time']}",
        f"**扫描路径**: {results['path']}",
        f"**扫描文件数**: {results['total_files']}",
        "",
        "## 扫描结果汇总",
        ""
    ]
    
    for scanner_name, scanner_data in results['scanners'].items():
        count = scanner_data['findings_count']
        lines.append(f"- **{scanner_name}**: {count} 个问题")
    
    lines.append("")
    lines.append("## 详细问题列表")
    lines.append("")
    
    # 敏感信息
    if results['scanners'].get('secret', {}).get('findings_count', 0) > 0:
        lines.append("### 🔐 敏感信息")
        lines.append("")
        for finding in results['scanners']['secret']['details'].get('all_findings', []):
            lines.append(f"- **文件**: {finding['file']}")
            lines.append(f"  - **类型**: {finding['type']}")
            lines.append(f"  - **行号**: {finding['line']}")
            lines.append(f"  - **匹配**: `{finding['match']}`")
            lines.append("")
    
    # 超长函数
    if results['scanners'].get('function_length', {}).get('findings_count', 0) > 0:
        lines.append("### 📏 超长函数")
        lines.append("")
        for finding in results['scanners']['function_length']['details'].get('all_functions', []):
            lines.append(f"- **函数**: `{finding['function_name']}`")
            lines.append(f"  - **文件**: {finding['file']}")
            lines.append(f"  - **行数**: {finding['line_count']} (行 {finding['start_line']}-{finding['end_line']})")
            lines.append("")
    
    # 未使用导入
    if results['scanners'].get('import', {}).get('findings_count', 0) > 0:
        lines.append("### 📦 未使用导入")
        lines.append("")
        for finding in results['scanners']['import']['details'].get('all_unused_imports', []):
            lines.append(f"- **导入**: `{finding['import_statement']}`")
            lines.append(f"  - **文件**: {finding['file']}")
            lines.append(f"  - **行号**: {finding['line_number']}")
            lines.append("")
    
    # TODO/FIXME
    if results['scanners'].get('todo', {}).get('findings_count', 0) > 0:
        lines.append("### ✅ TODO/FIXME")
        lines.append("")
        for finding in results['scanners']['todo']['details'].get('all_todos', []):
            age_status = "⚠️ 超过7天" if finding.get('over_7_days') else "✨ 新建"
            lines.append(f"- **内容**: `{finding['content']}`")
            lines.append(f"  - **文件**: {finding['file']}")
            lines.append(f"  - **行号**: {finding['line']}")
            lines.append(f"  - **状态**: {age_status}")
            lines.append("")
    
    return "\n".join(lines)


if __name__ == '__main__':
    main()