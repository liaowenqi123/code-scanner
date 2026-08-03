"""
FunctionLengthScanner - 函数长度检测（修复版）
"""

import ast
from typing import List, Dict
from pathlib import Path


class FunctionLengthScanner:
    """检测超过指定行数的函数"""

    def __init__(self, max_lines: int = 80):
        self.max_lines = max_lines

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件中的超长函数"""
        results = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return results

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 计算函数的结束行
                end_line = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
                start_line = node.lineno
                line_count = end_line - start_line + 1

                if line_count > self.max_lines:
                    results.append({
                        "file": file_path,
                        "function_name": node.name,
                        "line_count": line_count,
                        "start_line": start_line,
                        "end_line": end_line
                    })

        return results

    def scan_directory(self, path: str) -> Dict:
        """扫描目录中的所有Python文件"""
        all_results = {
            "total_files": 0,
            "files_scanned": [],
            "all_functions": []
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
                all_results["all_functions"].extend(findings)
            except (IOError, UnicodeDecodeError):
                continue

        return all_results