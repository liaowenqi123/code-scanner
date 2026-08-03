"""pytest配置文件"""

import sys
from pathlib import Path

# 将src目录添加到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))