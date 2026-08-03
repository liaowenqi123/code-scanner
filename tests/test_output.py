"""输出渲染冒烟测试：HTML / Markdown / finding 统一提取"""

from code_scanner.output.html import render_html
from code_scanner.output.markdown import render_markdown
from code_scanner.output import finding_parts


def _sample_results() -> dict:
    return {
        "scan_time": "2026-01-01T00:00:00",
        "path": "/tmp/project",
        "total_files": 2,
        "quality_score": 62,
        "severity_distribution": {"high": 1, "medium": 2, "low": 3},
        "scanners": {
            "secret": {
                "findings_count": 1,
                "findings": [{
                    "file": "/tmp/a.py", "line": 5, "severity": "high",
                    "type": "AWS_ACCESS_KEY", "match": "AKIA123",
                }],
                "details": {},
            },
            "comments": {
                "findings_count": 1,
                "findings": [{
                    "file": "/tmp/a.py", "line": 1, "severity": "low",
                    "type": "missing_docstring", "message": "缺少docstring", "name": "foo",
                }],
                "details": {},
            },
        },
    }


class TestMarkdownRender:
    def test_contains_key_sections(self):
        md = render_markdown(_sample_results())
        assert "质量评分" in md
        assert "62/100" in md
        assert "| 扫描器 |" in md
        assert "AWS_ACCESS_KEY" in md
        assert "缺少docstring" in md


class TestHtmlRender:
    def test_contains_key_sections(self):
        html = render_html(_sample_results())
        assert "<!DOCTYPE html>" in html
        assert "62/100" in html
        assert "AWS_ACCESS_KEY" in html
        assert "missing_docstring" in html

    def test_escapes_html(self):
        results = _sample_results()
        results["scanners"]["secret"]["findings"][0]["message"] = "<script>alert(1)</script>"
        html = render_html(results)
        assert "<script>alert" not in html


class TestFindingParts:
    def test_legacy_import_finding(self):
        line, title, desc = finding_parts({
            "file": "x", "line_number": 3,
            "import_statement": "import os", "import_name": "os",
        })
        assert line == 3
        assert title == "os"
        assert desc == "import os"

    def test_function_length_finding(self):
        line, title, desc = finding_parts({
            "file": "x", "function_name": "foo",
            "line_count": 100, "start_line": 1, "end_line": 100,
        })
        assert line == 1
        assert title == "foo"
        assert "100 行" in desc

    def test_new_style_finding(self):
        line, title, desc = finding_parts({
            "file": "x", "line": 7, "type": "magic_number",
            "message": "魔法数字 42",
        })
        assert line == 7
        assert title == "magic_number"
        assert desc == "魔法数字 42"
