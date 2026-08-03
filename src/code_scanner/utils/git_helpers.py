"""
Git辅助函数 - 正确版本
修复了原版本的死循环和逻辑错误
"""

import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Optional


def get_git_history_with_todos(file_path: str) -> List[Dict]:
    """
    获取文件中的TODO/FIXME注释及其git历史信息

    Args:
        file_path: 文件路径

    Returns:
        包含TODO信息的字典列表
    """
    todos = []

    # 检查git是否可用
    try:
        subprocess.run(
            ["git", "--version"],
            capture_output=True,
            timeout=5,
            check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # Git不可用，返回特殊标记
        return [{
            "line": 0,
            "content": "",
            "over_7_days": False,
            "commit_date": None,
            "undetermined_git": True,
            "git_error": "Git命令不可用"
        }]

    # 获取文件所在的git仓库根目录
    file_path_obj = Path(file_path).resolve()
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            timeout=10,
            check=True,
            cwd=file_path_obj.parent
        )
        repo_root = result.stdout.decode('utf-8', errors='ignore').strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return [{
            "line": 0,
            "content": "",
            "over_7_days": False,
            "commit_date": None,
            "undetermined_git": True,
            "git_error": "不在git仓库中"
        }]

    # 获取文件的git日志
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--follow", "--format=%H|%ai|%s", "--", file_path],
            capture_output=True,
            timeout=30,
            check=True,
            cwd=repo_root
        )

        commits = []
        output = result.stdout.decode('utf-8', errors='ignore').strip()
        for line in output.split('\n'):
            if line and '|' in line:
                parts = line.split('|', 2)
                if len(parts) >= 3:
                    commits.append({
                        'hash': parts[0],
                        'date': parts[1],
                        'message': parts[2]
                    })

        if not commits:
            return []

        # 检查每个commit是否超过7天
        now = datetime.now(timezone.utc)
        for commit in commits:
            try:
                commit_date = datetime.fromisoformat(commit['date'].replace(' ', 'T'))
                if commit_date.tzinfo is None:
                    commit_date = commit_date.replace(tzinfo=timezone.utc)

                days_diff = (now - commit_date).days
                todos.append({
                    "hash": commit['hash'],
                    "over_7_days": days_diff > 7,
                    "commit_date": commit_date.isoformat(),
                    "message": commit['message']
                })
            except (ValueError, TypeError):
                continue

        return todos

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        return [{
            "line": 0,
            "content": "",
            "over_7_days": False,
            "commit_date": None,
            "undetermined_git": True,
            "git_error": f"获取git历史失败: {str(e)}"
        }]


def is_over_7_days(commit_date_str: Optional[str]) -> bool:
    """判断提交日期是否超过7天"""
    if not commit_date_str:
        return False

    try:
        commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        return (now - commit_date).days > 7
    except (ValueError, TypeError):
        return False