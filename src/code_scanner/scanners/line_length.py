"""
LineLengthScanner - 超长行检测
"""

from typing import List, Dict
from pathlib import Path


class LineLengthScanner:
    """检测超过指定长度的代码行"""

    def __init__(self, max_length: int = 120):
        self.max_length = max_length

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件中的超长行"""
        results = []
        lines = content.split('\n')

        for idx, line in enumerate(lines, start=1):
            length = len(line)
            if length > self.max_length:
                results.append({
                    "file": file_path,
                    "line": idx,
                    "severity": "low",
                    "type": "line_too_long",
                    "message": f"行长为 {length} 字符（阈值 {self.max_length}）",
                    "length": length,
                    "content": line.strip()[:100],
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
