"""ImportScanner测试"""

import pytest
from code_scanner.scanners.imports import ImportScanner


class TestImportScanner:
    def test_unused_import(self):
        """测试未使用的导入"""
        scanner = ImportScanner()
        content = '''
import os
import sys

def hello():
    print("Hello")
'''
        results = scanner.scan_file("test.py", content)

        assert len(results) == 2

    def test_used_import(self):
        """测试已使用的导入"""
        scanner = ImportScanner()
        content = '''
import os

def getcwd():
    return os.getcwd()
'''
        results = scanner.scan_file("test.py", content)

        assert len(results) == 0

    def test_syntax_error(self):
        """测试语法错误的文件"""
        scanner = ImportScanner()
        content = "import os\n\ndef broken(\n"

        results = scanner.scan_file("test.py", content)

        assert len(results) == 0