"""TodoScanner测试"""

import pytest
from code_scanner.scanners.todo import TodoScanner


class TestTodoScanner:
    def test_todo_detection(self):
        """测试TODO检测"""
        scanner = TodoScanner()
        content = "# TODO: implement this"
        results = scanner.scan_file("test.py", content)

        assert len(results) > 0
        assert "implement this" in results[0]["content"]

    def test_fixme_detection(self):
        """测试FIXME检测"""
        scanner = TodoScanner()
        content = "# FIXME: fix this bug"
        results = scanner.scan_file("test.py", content)

        assert len(results) > 0
        assert "fix this bug" in results[0]["content"]

    def test_no_todos(self):
        """测试无TODO的代码"""
        scanner = TodoScanner()
        content = '''
def hello():
    print("Hello")
    return 42
'''
        results = scanner.scan_file("test.py", content)

        assert len(results) == 0