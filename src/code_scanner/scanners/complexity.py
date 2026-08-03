"""
ComplexityScanner - 圈复杂度与嵌套深度检测
参考 McCabe 复杂度度量：每个 if/elif/for/while/except/with/assert/布尔运算符等控制流都会增加复杂度。
"""

import ast
from typing import List, Dict
from pathlib import Path


class ComplexityScanner:
    """检测高圈复杂度函数和过深嵌套"""

    def __init__(self, max_complexity: int = 10, max_depth: int = 5):
        self.max_complexity = max_complexity
        self.max_depth = max_depth

    def _calc_complexity(self, node: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                # 每个 and/or 都增加一个分支
                complexity += len(child.values) - 1
            elif isinstance(child, ast.IfExp):
                complexity += 1
        return complexity

    def _max_depth(self, node: ast.AST) -> int:
        """计算最大嵌套深度"""
        max_depth = 0

        def visit(n, depth):
            nonlocal max_depth
            max_depth = max(max_depth, depth)
            for child in ast.iter_child_nodes(n):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor,
                                      ast.Try, ast.With, ast.FunctionDef, ast.AsyncFunctionDef)):
                    visit(child, depth + 1)
                else:
                    visit(child, depth)

        visit(node, 0)
        return max_depth

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件中的复杂函数"""
        results = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return results

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            complexity = self._calc_complexity(node)
            depth = self._max_depth(node)

            if complexity > self.max_complexity:
                results.append({
                    "file": file_path,
                    "line": node.lineno,
                    "severity": "high",
                    "type": "high_complexity",
                    "message": f"函数 '{node.name}' 圈复杂度为 {complexity}（阈值 {self.max_complexity}）",
                    "function_name": node.name,
                    "complexity": complexity,
                })

            if depth > self.max_depth:
                results.append({
                    "file": file_path,
                    "line": node.lineno,
                    "severity": "medium",
                    "type": "deep_nesting",
                    "message": f"函数 '{node.name}' 最大嵌套深度为 {depth}（阈值 {self.max_depth}）",
                    "function_name": node.name,
                    "depth": depth,
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
