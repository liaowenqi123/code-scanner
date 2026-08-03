"""CommentsScanner 与 DuplicateCodeScanner 测试"""

import pytest
from code_scanner.scanners.comments import CommentsScanner
from code_scanner.scanners.duplicate import DuplicateCodeScanner


class TestCommentsScanner:
    def test_low_comment_ratio(self):
        """注释比例过低应告警"""
        scanner = CommentsScanner(min_ratio=0.10)
        code_lines = "\n".join(f"result_{i} = {i}" for i in range(20))
        content = code_lines + "\n# 只有一行注释\n"
        results = scanner.scan_file("test.py", content)
        low = [r for r in results if r["type"] == "low_comment_ratio"]
        assert len(low) == 1
        assert low[0]["severity"] == "medium"

    def test_high_comment_ratio(self):
        """注释比例过高应告警"""
        scanner = CommentsScanner(max_ratio=0.50)
        lines = ["# 注释" + str(i) for i in range(10)] + ["x = 1"]
        content = "\n".join(lines)
        results = scanner.scan_file("test.py", content)
        high = [r for r in results if r["type"] == "high_comment_ratio"]
        assert len(high) == 1
        assert high[0]["severity"] == "low"

    def test_missing_docstring(self):
        """公开函数缺少 docstring 应告警"""
        scanner = CommentsScanner()
        content = '''
"""模块 docstring"""

def public_func():
    return 1
'''
        results = scanner.scan_file("test.py", content)
        missing = [r for r in results if r["type"] == "missing_docstring"]
        assert len(missing) == 1
        assert missing[0]["name"] == "public_func"

    def test_with_docstring(self):
        """有 docstring 的公开函数不应告警"""
        scanner = CommentsScanner()
        content = '''
"""模块 docstring"""

def documented():
    """函数说明"""
    return 1
'''
        results = scanner.scan_file("test.py", content)
        missing = [r for r in results if r["type"] == "missing_docstring"]
        assert len(missing) == 0


class TestDuplicateCodeScanner:
    def test_duplicate_functions(self):
        """结构相同的函数应告警"""
        scanner = DuplicateCodeScanner(min_statements=3)
        content = '''
def add_one(x):
    a = x + 1
    b = a * 2
    return b

def add_two(y):
    a = y + 1
    b = a * 2
    return b
'''
        results = scanner.scan_file("test.py", content)
        dup = [r for r in results if r["type"] == "duplicate_code"]
        assert len(dup) == 1
        assert dup[0]["severity"] == "medium"
        assert len(dup[0]["function_names"]) == 2

    def test_distinct_functions(self):
        """结构不同的函数不应告警"""
        scanner = DuplicateCodeScanner(min_statements=3)
        content = '''
def square(x):
    a = x * x
    b = a + 1
    return b

def reverse(s):
    a = s[::-1]
    b = a.upper()
    return b
'''
        results = scanner.scan_file("test.py", content)
        dup = [r for r in results if r["type"] == "duplicate_code"]
        assert len(dup) == 0

    def test_short_functions_ignored(self):
        """短函数不参与重复检测"""
        scanner = DuplicateCodeScanner(min_statements=3)
        content = '''
def noop_one():
    return 1

def noop_two():
    return 1
'''
        results = scanner.scan_file("test.py", content)
        dup = [r for r in results if r["type"] == "duplicate_code"]
        assert len(dup) == 0
