"""质量等级与评分工具"""

from typing import Dict, Tuple

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


SEVERITY_RICH = {"high": "bold red", "medium": "yellow", "low": "green"}
SEVERITY_LABEL = {"high": "高", "medium": "中", "low": "低"}
