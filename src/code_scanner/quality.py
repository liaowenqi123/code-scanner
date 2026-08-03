"""质量等级与评分工具

评分机制：类别分档 + 加权汇总。
每个扫描器类别按问题严重程度（high=5/medium=3/low=1）加权计数后分档打分，
再按类别重要性权重加权平均，避免单一类别问题把总分打到 0。
"""

from typing import Dict, Tuple

# 严重级别权重（类别内加权计数用）
SEVERITY_WEIGHTS = {"high": 5, "medium": 3, "low": 1}

# 类别重要性权重
SCANNER_WEIGHTS = {
    "secret": 3,
    "error_handling": 2,
    "complexity": 2,
    "structure": 1.5,
    "duplicate": 1.5,
    "function_length": 1.5,
    "import": 1,
    "line_length": 1,
    "naming": 1,
    "magic_number": 1,
    "comments": 1,
    "todo": 1,
}

# (最低分数, emoji, 等级名, 描述, rich颜色, html颜色)
LEVELS: Tuple[Tuple[int, str, str, str, str, str], ...] = (
    (90, "🌟", "卓越", "代码质量极佳", "green", "#3fb950"),
    (75, "😊", "良好", "有少量小问题", "green", "#3fb950"),
    (60, "🙂", "一般", "存在值得关注的问题", "yellow", "#d29922"),
    (40, "😷", "较差", "问题较多，建议整改", "orange", "#d29922"),
    (20, "💩", "糟糕", "大量问题，需要重构", "red", "#f85149"),
    (0, "☣️", "危险", "急需全面整改", "red", "#f85149"),
)


def get_quality_level(score: int) -> Dict:
    """根据分数（0-100）返回质量等级信息"""
    for threshold, emoji, name, desc, rich_color, html_color in LEVELS:
        if score >= threshold:
            return {
                "emoji": emoji,
                "name": name,
                "desc": desc,
                "rich_color": rich_color,
                "html_color": html_color,
            }
    return {
        "emoji": LEVELS[-1][1],
        "name": LEVELS[-1][2],
        "desc": LEVELS[-1][3],
        "rich_color": LEVELS[-1][4],
        "html_color": LEVELS[-1][5],
    }


def _category_score(weighted_count: int) -> int:
    """按类别加权计数分档打分（0-100）"""
    if weighted_count <= 0:
        return 100
    if weighted_count <= 5:
        return 92
    if weighted_count <= 12:
        return 82
    if weighted_count <= 20:
        return 70
    if weighted_count <= 30:
        return 56
    if weighted_count <= 45:
        return 40
    return 30


def compute_score(results: dict) -> Tuple[int, Dict]:
    """计算质量总分（0-100）和严重级别分布

    results: 含 scanners 字段（每个 scanner 有 findings 列表）的扫描结果
    """
    distribution = {"high": 0, "medium": 0, "low": 0}
    weighted_by_scanner = {}

    for scanner_name, scanner_data in results.get("scanners", {}).items():
        weighted = 0
        for finding in scanner_data.get("findings", []):
            severity = finding.get("severity", "low")
            if severity not in distribution:
                severity = "low"
            distribution[severity] += 1
            weighted += SEVERITY_WEIGHTS[severity]
        weighted_by_scanner[scanner_name] = weighted

    if not weighted_by_scanner:
        return 100, distribution

    total_weight = sum(SCANNER_WEIGHTS.get(name, 1) for name in weighted_by_scanner)
    weighted_sum = sum(
        _category_score(weighted) * SCANNER_WEIGHTS.get(name, 1)
        for name, weighted in weighted_by_scanner.items()
    )
    score = round(weighted_sum / total_weight) if total_weight else 100
    return score, distribution


SEVERITY_RICH = {"high": "bold red", "medium": "yellow", "low": "green"}
SEVERITY_LABEL = {"high": "高", "medium": "中", "low": "低"}
