"""
TodoScanner - TODO/FIXME注释检测（修复版）
"""

import re
from typing import List, Dict
from pathlib import Path

from ..utils.git_helpers import get_git_history_with_todos, is_over_7_days


class TodoScanner:
    """检测TODO/FIXME注释及其年龄"""

    PATTERNS = [
        r"#\s*TODO[:\s](.+)$",
        r"#\s*FIXME[:\s](.+)$",
        r"//\s*TODO[:\s](.+)$",
        r"//\s*FIXME[:\s](.+)$",
    ]

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件中的TODO/FIXME注释"""
        results = []
        lines = content.split('\n')

        # 获取git历史（可能失败）
        git_info = get_git_history_with_todos(file_path)
        has_git = not (git_info and git_info[0].get("undetermined_git", False))

        for line_num, line in enumerate(lines, start=1):
            for pattern in self.PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    todo_content = match.group(1).strip()

                    result = {
                        "file": file_path,
                        "line": line_num,
                        "content": todo_content,
                        "over_7_days": False,
                        "commit_date": None,
                        "undetermined_git": not has_git
                    }

                    # 如果有git信息，检查年龄
                    if has_git and git_info:
                        # 简化处理：使用第一个有效的git信息
                        for info in git_info:
                            if info.get("commit_date"):
                                result["over_7_days"] = is_over_7_days(info["commit_date"])
                                result["commit_date"] = info["commit_date"]
                                break

                    results.append(result)
                    break  # 只匹配第一个模式

        return results

    def scan_directory(self, path: str) -> Dict:
        """扫描目录中的所有Python文件"""
        all_results = {
            "total_files": 0,
            "files_scanned": [],
            "all_todos": []
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
                all_results["all_todos"].extend(findings)
            except (IOError, UnicodeDecodeError):
                continue

        return all_results