"""FunctionLengthScanner测试"""

import pytest
from code_scanner.scanners.function_length import FunctionLengthScanner


class TestFunctionLengthScanner:
    def test_short_function(self):
        """测试短函数"""
        scanner = FunctionLengthScanner(max_lines=10)
        content = '''
def short():
    x = 1
    return x
'''
        results = scanner.scan_file("test.py", content)

        assert len(results) == 0

    def test_long_function(self):
        """测试长函数"""
        scanner = FunctionLengthScanner(max_lines=5)
        lines = ["    x = {}".format(i) for i in range(10)]
        content = "def long():\n" + "\n".join(lines)

        results = scanner.scan_file("test.py", content)

        assert len(results) > 0
        assert results[0]["function_name"] == "long"

    def test_syntax_error(self):
        """测试语法错误的文件"""
        scanner = FunctionLengthScanner()
        content = "def broken(\n"  # 语法错误

        results = scanner.scan_file("test.py", content)

        assert len(results) == 0