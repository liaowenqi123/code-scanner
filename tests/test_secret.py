"""SecretScanner测试"""

import pytest
from code_scanner.scanners.secret import SecretScanner


class TestSecretScanner:
    def test_aws_key_detection(self):
        """测试AWS密钥检测"""
        scanner = SecretScanner()
        content = 'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"'
        results = scanner.scan_file("test.py", content)

        assert len(results) > 0
        assert any(r["type"] == "AWS_ACCESS_KEY" for r in results)

    def test_github_token_detection(self):
        """测试GitHub Token检测"""
        scanner = SecretScanner()
        content = 'token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"'
        results = scanner.scan_file("test.py", content)

        assert len(results) > 0
        assert any(r["type"] == "GITHUB_TOKEN" for r in results)

    def test_no_secrets(self):
        """测试无敏感信息的代码"""
        scanner = SecretScanner()
        content = '''
def hello():
    print("Hello World")
    return 42
'''
        results = scanner.scan_file("test.py", content)

        assert len(results) == 0