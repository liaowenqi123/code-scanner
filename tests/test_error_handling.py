"""ErrorHandlingScanner 与 NamingScanner 测试"""

import pytest
from code_scanner.scanners.error_handling import ErrorHandlingScanner
from code_scanner.scanners.naming import NamingScanner


class TestErrorHandlingScanner:
    def test_bare_except(self):
        """裸 except 应告警"""
        scanner = ErrorHandlingScanner()
        content = '''
def f():
    try:
        x = 1
    except:
        print("error")
'''
        results = scanner.scan_file("test.py", content)
        bare = [r for r in results if r["type"] == "bare_except"]
        assert len(bare) == 1
        assert bare[0]["severity"] == "high"

    def test_swallowed_exception(self):
        """except 后直接 pass 应告警"""
        scanner = ErrorHandlingScanner()
        content = '''
def f():
    try:
        x = 1
    except Exception:
        pass
'''
        results = scanner.scan_file("test.py", content)
        swallowed = [r for r in results if r["type"] == "swallowed_exception"]
        assert len(swallowed) == 1
        assert swallowed[0]["severity"] == "high"

    def test_proper_handling(self):
        """正常错误处理不应告警"""
        scanner = ErrorHandlingScanner()
        content = '''
def f():
    try:
        x = int("abc")
    except ValueError as e:
        print(e)
'''
        results = scanner.scan_file("test.py", content)
        assert len(results) == 0

    def test_broad_except(self):
        """宽泛捕获 Exception 且无变量应告警"""
        scanner = ErrorHandlingScanner()
        content = '''
def f():
    try:
        x = 1
    except Exception:
        print("error")
'''
        results = scanner.scan_file("test.py", content)
        broad = [r for r in results if r["type"] == "broad_except"]
        assert len(broad) == 1
        assert broad[0]["severity"] == "medium"


class TestNamingScanner:
    def test_bad_function_name(self):
        """驼峰函数名应告警"""
        scanner = NamingScanner()
        content = '''
def BadFunctionName():
    return 1
'''
        results = scanner.scan_file("test.py", content)
        bad = [r for r in results if r["type"] == "bad_function_name"]
        assert len(bad) == 1
        assert bad[0]["name"] == "BadFunctionName"

    def test_bad_class_name(self):
        """小写类名应告警"""
        scanner = NamingScanner()
        content = '''
class bad_class:
    pass
'''
        results = scanner.scan_file("test.py", content)
        bad = [r for r in results if r["type"] == "bad_class_name"]
        assert len(bad) == 1

    def test_bad_constant_name(self):
        """模块级小写常量应告警"""
        scanner = NamingScanner()
        content = 'version = "1.0.0"\n'
        results = scanner.scan_file("test.py", content)
        bad = [r for r in results if r["type"] == "bad_constant_name"]
        assert len(bad) == 1
        assert bad[0]["name"] == "version"

    def test_dunder_method_ok(self):
        """dunder 方法名不应告警"""
        scanner = NamingScanner()
        content = '''
class Foo:
    def __init__(self):
        pass
'''
        results = scanner.scan_file("test.py", content)
        bad = [r for r in results if r["type"] == "bad_function_name"]
        assert len(bad) == 0

    def test_clean_code(self):
        """规范命名不应告警"""
        scanner = NamingScanner()
        content = '''
class UserService:
    def get_user_name(self):
        return "name"
'''
        results = scanner.scan_file("test.py", content)
        assert len(results) == 0
