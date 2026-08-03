"""质量评分算法测试"""

from code_scanner.quality import compute_score, get_quality_level, _category_score


def _make_results(per_scanner=None):
    """构造扫描结果，per_scanner: {扫描器名: [(severity, count)]}"""
    scanners = {}
    for name, findings_spec in (per_scanner or {}).items():
        findings = []
        for severity, count in findings_spec:
            findings.extend([{"severity": severity, "type": "x"} for _ in range(count)])
        scanners[name] = {"findings_count": len(findings), "findings": findings, "details": {}}
    return {"scanners": scanners}


class TestCategoryScore:
    def test_band_boundaries(self):
        assert _category_score(0) == 100
        assert _category_score(5) == 92
        assert _category_score(12) == 82
        assert _category_score(20) == 70
        assert _category_score(30) == 56
        assert _category_score(45) == 40
        assert _category_score(100) == 30

    def test_floor_not_zero(self):
        """问题再多类别得分也不低于 30，总分不会被打到 0"""
        assert _category_score(999) >= 30


class TestComputeScore:
    def test_clean_project_scores_100(self):
        score, dist = compute_score(_make_results({"secret": [], "complexity": []}))
        assert score == 100
        assert dist == {"high": 0, "medium": 0, "low": 0}

    def test_low_impact_not_zero(self):
        """大量低危问题（如缺 docstring）不应把总分打到 0"""
        results = _make_results({
            "comments": [("low", 50)],
        })
        score, dist = compute_score(results)
        assert score >= 30
        assert dist["low"] == 50

    def test_high_risk_weighs_more(self):
        """同样数量下，高危问题（high 加权）应比低危问题扣分更重"""
        with_high = _make_results({"secret": [("high", 2)]})
        with_low = _make_results({"secret": [("low", 2)]})
        score_high, _ = compute_score(with_high)
        score_low, _ = compute_score(with_low)
        # 2 个 high(加权10) 落入更高扣分档，比 2 个 low(加权2) 分数低
        assert score_high < score_low

    def test_multi_category_averaging(self):
        """多类别时按权重加权平均，坏类别不会拖垮总分"""
        results = _make_results({
            "secret": [("high", 50)],       # 类别得分 30
            "complexity": [],               # 类别得分 100
        })
        score, _ = compute_score(results)
        # (30*3 + 100*2) / 5 = 58
        assert score == 58

    def test_empty_results(self):
        score, dist = compute_score({"scanners": {}})
        assert score == 100
        assert dist["high"] == 0


class TestQualityLevel:
    def test_level_boundaries(self):
        assert get_quality_level(100)["name"] == "卓越"
        assert get_quality_level(75)["name"] == "良好"
        assert get_quality_level(60)["name"] == "一般"
        assert get_quality_level(40)["name"] == "较差"
        assert get_quality_level(20)["name"] == "糟糕"
        assert get_quality_level(0)["name"] == "危险"

    def test_level_has_emoji_and_color(self):
        level = get_quality_level(62)
        assert level["emoji"]
        assert level["html_color"]
