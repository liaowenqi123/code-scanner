"""
SecretScanner - 敏感信息检测（修复版）
"""

import re
from typing import List, Dict
from pathlib import Path


class SecretScanner:
    """检测硬编码的密码、API Key等敏感信息"""

    PATTERNS = [
        ("AWS_ACCESS_KEY", r"AKIA[0-9A-Z]{16}", "AWS Access Key ID"),
        ("GITHUB_TOKEN", r"gh[pousr]_[a-zA-Z0-9]{36,}", "GitHub Personal Access Token"),
        ("API_KEY", r"(?:sk|pk)-[a-zA-Z0-9]{32,}", "API Key (OpenAI etc)"),
        ("PASSWORD", r"(?:password|passwd|pwd)\s*[=:]\s*['\"]?[^\s'\"]{4,}['\"]?", "Hardcoded Password"),
        ("PRIVATE_KEY", r"-----BEGIN (?:RSA )?PRIVATE KEY-----", "Private Key"),
    ]

    def scan_file(self, file_path: str, content: str) -> List[Dict]:
        """扫描文件内容中的敏感信息"""
        results = []
        lines = content.split('\n')

        for pattern_name, pattern_regex, description in self.PATTERNS:
            try:
                pattern = re.compile(pattern_regex, re.IGNORECASE if pattern_name == "PASSWORD" else 0)
                for match in pattern.finditer(content):
                    # 计算行号
                    line_num = content[:match.start()].count('\n') + 1

                    results.append({
                        "file": file_path,
                        "type": pattern_name,
                        "description": description,
                        "match": match.group()[:50],  # 只显示前50个字符
                        "line": line_num
                    })
            except re.error:
                continue

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
            # 跳过隐藏目录
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