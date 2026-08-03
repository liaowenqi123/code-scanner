"""MagicNumberScanner 与 StructureScanner 测试"""

import pytest
from code_scanner.scanners.magic_number import MagicNumberScanner
from code_scanner.scanners.structure import StructureScanner


class TestMagicNumberScanner:
    def test_magic_number(self):
        """函数体内裸数字应告警"""
        scanner = MagicNumberScanner()
        content = '''
import time

def f():
    time.sleep(5)
    return 42
'''
        results = scanner.scan_file("test.py", content)
        assert len(results) >= 2  # 5 和 42
        assert all(r["type"] == "magic_number" for r in results)
        assert all(r["severity"] == "medium" for r in results)

    def test_ignored_values(self):
        """常见默认值 0/1/100 不应告警"""
        scanner = MagicNumberScanner()
        content = '''
def f(items):
    total = 0
    count = 1
    percent = 100
    return items[0]
'''
        results = scanner.scan_file("test.py", content)
        assert len(results) == 0

    def test_assignment_skipped(self):
        """赋值给变量的数字不算魔法数字"""
        scanner = MagicNumberScanner()
        content = '''
def f():
    timeout = 30
    return timeout
'''
        results = scanner.scan_file("test.py", content)
        assert len(results) == 0

    def test_syntax_error(self):
        """语法错误的文件应返回空"""
        scanner = MagicNumberScanner()
        results = scanner.scan_file("test.py", "def broken(\n")
        assert len(results) == 0


class TestStructureScanner:
    def test_mutable_default(self):
        """可变默认参数应告警"""
        scanner = StructureScanner()
        content = '''
def f(items=[]):
    items.append(1)
    return items
'''
        results = scanner.scan_file("test.py", content)
        mutable = [r for r in results if r["type"] == "mutable_default_arg"]
        assert len(mutable) == 1
        assert mutable[0]["severity"] == "high"

    def test_too_many_arguments(self):
        """参数过多应告警"""
        scanner = StructureScanner(max_args=3)
        content = '''
def f(a, b, c, d):
    return a + b + c + d
'''
        results = scanner.scan_file("test.py", content)
        too_many = [r for r in results if r["type"] == "too_many_arguments"]
        assert len(too_many) == 1
        assert too_many[0]["severity"] == "medium"
        assert too_many[0]["arg_count"] == 4

    def test_global_statement(self):
        """global 语句应告警"""
        scanner = StructureScanner()
        content = '''
counter = 0

def f():
    global counter
    counter += 1
'''
        results = scanner.scan_file("test.py", content)
        global_findings = [r for r in results if r["type"] == "global_statement"]
        assert len(global_findings) == 1
        assert global_findings[0]["severity"] == "low"

    def test_clean_code(self):
        """正常代码不应告警"""
        scanner = StructureScanner()
        content = '''
def f(a, b=1):
    return a + b
'''
        results = scanner.scan_file("test.py", content)
        assert len(results) == 0
