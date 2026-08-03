"""
ImportScanner - 未使用导入检测（修复版）
修复了原版本的逻辑错误：收集的是使用的名称而非定义的名称
"""

import ast
from typing import List, Dict, Set
from pathlib import Path


class ImportScanner:
    """检测未被使用的import语句"""

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件中的未使用导入"""
        results = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return results

        # 收集所有导入的模块
        imports = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = {
                        "line": node.lineno,
                        "statement": content.split('\n')[node.lineno - 1].strip()
                    }
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports[name] = {
                        "line": node.lineno,
                        "statement": content.split('\n')[node.lineno - 1].strip()
                    }

        # 收集所有使用的名称（关键修复！）
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                used_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                # 处理属性访问，如 os.path
                if isinstance(node.value, ast.Name):
                    used_names.add(node.value.id)

        # 检查哪些导入未被使用
        for name, info in imports.items():
            if name not in used_names:
                results.append({
                    "file": file_path,
                    "import_name": name,
                    "import_statement": info["statement"],
                    "line_number": info["line"]
                })

        return results

    def scan_directory(self, path: str) -> Dict:
        """扫描目录中的所有Python文件"""
        all_results = {
            "total_files": 0,
            "files_scanned": [],
            "all_unused_imports": []
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
                all_results["all_unused_imports"].extend(findings)
            except (IOError, UnicodeDecodeError):
                continue

        return all_results