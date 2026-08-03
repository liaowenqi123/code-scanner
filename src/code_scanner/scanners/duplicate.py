"""
DuplicateCodeScanner - 重复代码检测
通过比较 AST 结构指纹检测结构重复的函数体。
"""

import ast
from typing import List, Dict, DefaultDict
from collections import defaultdict
from pathlib import Path


class DuplicateCodeScanner:
    """检测结构重复的函数体"""

    def __init__(self, min_statements: int = 3):
        # 函数体至少包含的语句数，避免 pass/单语句函数误报
        self.min_statements = min_statements

    @staticmethod
    def _fingerprint(node) -> str:
        """生成函数 AST 指纹（忽略函数名、参数名、行号等）"""
        import copy
        clone = copy.deepcopy(node)
        clone.name = "func"
        # 参数名统一为占位符，避免仅因参数名不同而漏报
        for arg in list(clone.args.posonlyargs) + list(clone.args.args) + list(clone.args.kwonlyargs):
            arg.arg = "arg"
        if clone.args.vararg is not None:
            clone.args.vararg.arg = "arg"
        if clone.args.kwarg is not None:
            clone.args.kwarg.arg = "arg"
        # 函数体内所有变量名统一为占位符，只比较代码结构
        for sub in ast.walk(clone):
            if isinstance(sub, ast.Name):
                sub.id = "var"
        # 只比较参数结构 + 函数体
        return ast.dump(clone, include_attributes=False, annotate_fields=False)

    @staticmethod
    def _count_statements(node) -> int:
        """统计函数体语句数（去掉 docstring）"""
        body = list(node.body)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            body = body[1:]
        return len(body)

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件中的重复函数"""
        results = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return results

        # 按指纹分组函数
        groups: DefaultDict[str, List] = defaultdict(list)
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if self._count_statements(node) < self.min_statements:
                continue
            fingerprint = self._fingerprint(node)
            groups[fingerprint].append(node)

        for fingerprint, funcs in groups.items():
            if len(funcs) < 2:
                continue
            # 只报告一次，描述所有重复函数
            first = funcs[0]
            func_names = "、".join(f"'{f.name}'" for f in funcs)
            results.append({
                "file": file_path,
                "line": first.lineno,
                "severity": "medium",
                "type": "duplicate_code",
                "message": f"函数 {func_names} 存在结构重复的代码（共 {len(funcs)} 处），建议提取公共逻辑",
                "function_names": [f.name for f in funcs],
                "locations": [f.lineno for f in funcs],
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
