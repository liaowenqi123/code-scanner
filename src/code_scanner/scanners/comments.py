"""
CommentsScanner - 注释质量检测
检测注释比例过低/过高的文件，以及缺少 docstring 的公开函数、类、模块。
"""

import ast
import re
from typing import List, Dict
from pathlib import Path

_COMMENT_RE = re.compile(r'^\s*#')
_WHITESPACE_RE = re.compile(r'^\s*$')


class CommentsScanner:
    """检测注释质量和缺失的 docstring"""

    def __init__(self, min_ratio: float = 0.10, max_ratio: float = 0.60):
        self.min_ratio = min_ratio
        self.max_ratio = max_ratio

    def _comment_ratio(self, content: str) -> float:
        """计算注释行占代码行的比例"""
        lines = content.split('\n')
        code_lines = 0
        comment_lines = 0
        for line in lines:
            stripped = line.strip()
            if _WHITESPACE_RE.match(stripped):
                continue
            if _COMMENT_RE.match(stripped):
                comment_lines += 1
            else:
                code_lines += 1
        total = code_lines + comment_lines
        return (comment_lines / total) if total else 0.0

    def _get_docstring(self, node) -> str:
        """获取节点 docstring"""
        body = getattr(node, 'body', None)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            return body[0].value.value
        return ""

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件中的注释问题"""
        results = []

        # 注释比例检查
        ratio = self._comment_ratio(content)
        if ratio < self.min_ratio and ratio > 0:
            results.append({
                "file": file_path,
                "line": 1,
                "severity": "medium",
                "type": "low_comment_ratio",
                "message": f"注释比例仅 {ratio:.0%}（阈值 {self.min_ratio:.0%}），建议补充注释说明代码意图",
                "ratio": round(ratio, 3),
            })
        elif ratio > self.max_ratio:
            results.append({
                "file": file_path,
                "line": 1,
                "severity": "low",
                "type": "high_comment_ratio",
                "message": f"注释比例高达 {ratio:.0%}（阈值 {self.max_ratio:.0%}），建议清理冗余注释",
                "ratio": round(ratio, 3),
            })

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return results

        # 模块级 docstring
        if not self._get_docstring(tree):
            results.append({
                "file": file_path,
                "line": 1,
                "severity": "low",
                "type": "missing_module_docstring",
                "message": "模块缺少 docstring，建议在文件开头说明用途",
            })

        # 函数/类 docstring（跳过私有和 dunder）
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and not node.name.startswith('_') and not (node.name.startswith('__') and node.name.endswith('__')):
                if not self._get_docstring(node):
                    results.append({
                        "file": file_path,
                        "line": node.lineno,
                        "severity": "low",
                        "type": "missing_docstring",
                        "message": f"公开函数 '{node.name}' 缺少 docstring",
                        "name": node.name,
                    })
            elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                if not self._get_docstring(node):
                    results.append({
                        "file": file_path,
                        "line": node.lineno,
                        "severity": "low",
                        "type": "missing_docstring",
                        "message": f"公开类 '{node.name}' 缺少 docstring",
                        "name": node.name,
                    })

        return results

    def scan_directory(self, path: str) -> Dict:
        """扫描目录中的所有Python文件"""
        all_results = {
            "total_files": 0,
            "files_scanned": [],
            "all_findings": []
        }

        path_obj = Path(path)
        if not path_obj.exists():
            return all_results

        for py_file in path_obj.rglob("*.py"):
            if any(part.startswith('.') for part in py_file.parts):
                continue

            try:
                content = py_file.read_text(encoding='utf-8')
                all_results["total_files"] += 1
                all_results["files_scanned"].append(str(py_file))

                findings = self.scan_file(str(py_file), content)
                all_results["all_findings"].extend(findings)
            except (IOError, UnicodeDecodeError):
                continue

        return all_results
