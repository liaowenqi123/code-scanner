"""
ErrorHandlingScanner - 错误处理检测
检测裸 except、吞掉异常的 except 块等问题。
"""

import ast
from typing import List, Dict
from pathlib import Path


class ErrorHandlingScanner:
    """检测错误处理中的常见问题"""

    def _is_pass_only(self, body: List[ast.stmt]) -> bool:
        """except 块是否只有 pass"""
        return len(body) == 1 and isinstance(body[0], ast.Pass)

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件中的错误处理问题"""
        results = []

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return results

        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue

            # 裸 except:（没有指定异常类型）
            if node.type is None:
                results.append({
                    "file": file_path,
                    "line": node.lineno,
                    "severity": "high",
                    "type": "bare_except",
                    "message": "裸 except: 会捕获包括 KeyboardInterrupt、SystemExit 在内的所有异常，建议指定具体异常类型",
                })
                continue

            # 捕获 Exception 但直接 pass（吞掉异常）
            if self._is_pass_only(node.body):
                exc_name = ""
                if isinstance(node.type, ast.Name):
                    exc_name = node.type.id
                results.append({
                    "file": file_path,
                    "line": node.lineno,
                    "severity": "high",
                    "type": "swallowed_exception",
                    "message": f"except {exc_name or '异常'} 后直接 pass，异常被静默吞掉，建议至少记录日志",
                    "exception": exc_name or "未知",
                })
            # 宽泛捕获 Exception，没有绑定异常变量
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception" and node.name is None:
                results.append({
                    "file": file_path,
                    "line": node.lineno,
                    "severity": "medium",
                    "type": "broad_except",
                    "message": "捕获宽泛的 Exception 且未绑定异常变量，建议缩小异常范围或使用 except Exception as e",
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
