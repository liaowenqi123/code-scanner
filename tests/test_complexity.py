"""ComplexityScanner 与 LineLengthScanner 测试"""

import pytest
from code_scanner.scanners.complexity import ComplexityScanner
from code_scanner.scanners.line_length import LineLengthScanner


class TestComplexityScanner:
    def test_simple_function(self):
        """简单函数不应告警"""
        scanner = ComplexityScanner(max_complexity=2)
        content = '''
def simple():
    x = 1
    return x
'''
        results = scanner.scan_file("test.py", content)
        assert len(results) == 0

    def test_high_complexity(self):
        """多分支函数应触发圈复杂度告警"""
        scanner = ComplexityScanner(max_complexity=2)
        content = '''
def complex_func(a):
    if a == 1:
        return "one"
    elif a == 2:
        return "two"
    elif a == 3:
        return "three"
    elif a == 4:
        return "four"
    elif a == 5:
        return "five"
    return "other"
'''
        results = scanner.scan_file("test.py", content)
        high = [r for r in results if r["type"] == "high_complexity"]
        assert len(high) == 1
        assert high[0]["function_name"] == "complex_func"
        assert high[0]["severity"] == "high"

    def test_deep_nesting(self):
        """深层嵌套应触发嵌套深度告警"""
        scanner = ComplexityScanner(max_depth=2)
        content = '''
def nested(a):
    for i in range(a):
        for j in range(a):
            for k in range(a):
                print(i, j, k)
'''
        results = scanner.scan_file("test.py", content)
        deep = [r for r in results if r["type"] == "deep_nesting"]
        assert len(deep) == 1
        assert deep[0]["severity"] == "medium"

    def test_syntax_error(self):
        """语法错误的文件应返回空"""
        scanner = ComplexityScanner()
        results = scanner.scan_file("test.py", "def broken(\n")
        assert len(results) == 0


class TestLineLengthScanner:
    def test_normal_lines(self):
        """正常长度行不应告警"""
        scanner = LineLengthScanner(max_length=120)
        content = "x = 1\n" * 10
        results = scanner.scan_file("test.py", content)
        assert len(results) == 0

    def test_long_line(self):
        """超长行应告警"""
        scanner = LineLengthScanner(max_length=20)
        content = 'some_variable = "this is a very long string value"\n'
        results = scanner.scan_file("test.py", content)
        assert len(results) == 1
        assert results[0]["type"] == "line_too_long"
        assert results[0]["severity"] == "low"
        assert results[0]["line"] == 1
