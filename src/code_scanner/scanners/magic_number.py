"""
MagicNumberScanner - 魔法数字检测
检测函数体中的未命名数字常量，建议提取为具名常量。
"""

import ast
from typing import List, Dict, Set
from pathlib import Path

# 常见且无害的默认值，不视为魔法数字
_IGNORED_VALUES: Set = {0, 1, -1, 2, 100}


class MagicNumberScanner:
    """检测函数体中的魔法数字"""

    def __init__(self, ignored: Set = None):
        self.ignored = ignored if ignored is not None else _IGNORED_VALUES

    def _is_ignored_context(self, node: ast.Constant, parent: ast.AST) -> bool:
        """判断数字是否出现在可忽略的上下文（赋值、索引等）"""
        # 赋值给变量：x = 100 视为已命名，跳过
        if isinstance(parent, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and parent.value is node:
            return True
        # 索引/切片：array[0]、lst[1:2]
        if isinstance(parent, ast.Subscript):
            return True
        # 属性访问链中的调用参数不跳过（如 time.sleep(5) 会报告）
        return False

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件函数体中的魔法数字"""
        results = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return results

        # 手动递归以便跟踪父节点
        def scan(node, parent):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) \
                    and not isinstance(node.value, bool) and node.value not in self.ignored:
                if not self._is_ignored_context(node, parent):
                    results.append({
                        "file": file_path,
                        "line": node.lineno,
                        "severity": "medium",
                        "type": "magic_number",
                        "message": f"魔法数字 {node.value!r}，建议提取为具名常量",
                        "value": node.value,
                    })
            for child in ast.iter_child_nodes(node):
                scan(child, node)

        # 只扫描函数/方法体，模块级常量赋值不算魔法数字
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for child in node.body:
                    scan(child, node)

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
