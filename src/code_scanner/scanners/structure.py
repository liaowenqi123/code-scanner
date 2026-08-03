"""
StructureScanner - 结构问题检测
检测可变默认参数、参数过多、global 语句使用。
"""

import ast
from typing import List, Dict
from pathlib import Path


class StructureScanner:
    """检测代码结构中的常见问题"""

    def __init__(self, max_args: int = 6):
        self.max_args = max_args

    @staticmethod
    def _is_mutable_default(default: ast.AST) -> bool:
        """判断默认值是否是可变的（list/dict/set）"""
        return isinstance(default, (ast.List, ast.Dict, ast.Set))

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件中的结构问题"""
        results = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return results

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # 可变默认参数
                all_defaults = list(node.args.defaults) + list(node.args.kw_defaults)
                for default in all_defaults:
                    if default is not None and self._is_mutable_default(default):
                        results.append({
                            "file": file_path,
                            "line": node.lineno,
                            "severity": "high",
                            "type": "mutable_default_arg",
                            "message": f"函数 '{node.name}' 使用可变对象作为默认参数，可能导致状态在多次调用间共享",
                            "function_name": node.name,
                        })
                        break

                # 参数过多
                arg_count = len(node.args.args)
                if arg_count > self.max_args:
                    results.append({
                        "file": file_path,
                        "line": node.lineno,
                        "severity": "medium",
                        "type": "too_many_arguments",
                        "message": f"函数 '{node.name}' 有 {arg_count} 个参数（阈值 {self.max_args}），建议拆分为对象或使用关键字参数",
                        "function_name": node.name,
                        "arg_count": arg_count,
                    })

            elif isinstance(node, ast.Global):
                results.append({
                    "file": file_path,
                    "line": node.lineno,
                    "severity": "low",
                    "type": "global_statement",
                    "message": "使用 global 语句，建议通过参数传递或返回值避免全局状态",
                    "names": list(node.names),
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
