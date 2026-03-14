"""
启动产品经理数据面板
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 设置 Streamlit 配置
os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

# 启动 Streamlit
import subprocess

app_path = Path(__file__).parent / "metrics_dashboard.py"

cmd = [
    sys.executable,
    "-m",
    "streamlit",
    "run",
    str(app_path),
    "--server.port",
    "8502",  # 使用 8502 端口，避免与主面板冲突
    "--server.address",
    "localhost",
    "--browser.serverAddress",
    "localhost",
    "--server.headless",
    "true",
]

print("=" * 80)
print("📊 产品经理数据面板")
print("=" * 80)
print()
print("正在启动数据面板服务...")
print()
print("访问地址：http://localhost:8502")
print()
print("提示：按 Ctrl+C 停止服务")
print()
print("=" * 80)
print()

try:
    subprocess.run(cmd)
except KeyboardInterrupt:
    print("\n")
    print("=" * 80)
    print("👋 数据面板已停止")
    print("=" * 80)
