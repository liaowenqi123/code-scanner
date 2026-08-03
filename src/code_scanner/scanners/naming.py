"""
NamingScanner - 命名规范检测
检查函数 snake_case、类 PascalCase、模块级常量 UPPER_SNAKE_CASE 等 PEP8 命名约定。
"""

import ast
import re
from typing import List, Dict
from pathlib import Path

_SNAKE_CASE_RE = re.compile(r'^[a-z_][a-z0-9_]*$')
_PASCAL_CASE_RE = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
_UPPER_SNAKE_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')


def _is_dunder(name: str) -> bool:
    return name.startswith('__') and name.endswith('__')


def _is_private(name: str) -> bool:
    return name.startswith('_')


class NamingScanner:
    """检测命名规范违规"""

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件中的命名问题"""
        results = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return results

        for node in ast.walk(tree):
            # 函数命名：snake_case（跳过 dunder 方法）
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not _is_dunder(node.name):
                if not _SNAKE_CASE_RE.match(node.name):
                    results.append({
                        "file": file_path,
                        "line": node.lineno,
                        "severity": "low",
                        "type": "bad_function_name",
                        "message": f"函数名 '{node.name}' 不符合 snake_case 命名规范",
                        "name": node.name,
                    })

            # 类命名：PascalCase
            elif isinstance(node, ast.ClassDef):
                if not _PASCAL_CASE_RE.match(node.name):
                    results.append({
                        "file": file_path,
                        "line": node.lineno,
                        "severity": "low",
                        "type": "bad_class_name",
                        "message": f"类名 '{node.name}' 不符合 PascalCase 命名规范",
                        "name": node.name,
                    })

        # 模块级常量：UPPER_SNAKE_CASE（只检查顶层赋值）
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and not _is_private(target.id) \
                            and not _UPPER_SNAKE_RE.match(target.id) \
                            and _looks_like_constant(node.value):
                        results.append({
                            "file": file_path,
                            "line": node.lineno,
                            "severity": "low",
                            "type": "bad_constant_name",
                            "message": f"模块级常量 '{target.id}' 不符合 UPPER_SNAKE_CASE 命名规范",
                            "name": target.id,
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


def _looks_like_constant(value: ast.AST) -> bool:
    """判断赋值右侧是否是常量值（数字/字符串/元组等）"""
    if isinstance(value, (ast.Constant, ast.Tuple)):
        return True
    if isinstance(value, ast.List) and value.elts and all(isinstance(e, ast.Constant) for e in value.elts):
        return True
    return False
