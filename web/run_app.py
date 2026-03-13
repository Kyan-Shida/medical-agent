"""
启动 Web 测试面板
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

app_path = Path(__file__).parent / "app.py"

cmd = [
    sys.executable,
    "-m",
    "streamlit",
    "run",
    str(app_path),
    "--server.port",
    "8501",
    "--server.address",
    "localhost",
    "--browser.serverAddress",
    "localhost",
    "--server.headless",
    "true",
]

print("=" * 80)
print("🏥 医疗 Agent Web 测试面板")
print("=" * 80)
print()
print("正在启动 Streamlit 服务...")
print()
print("访问地址：http://localhost:8501")
print()
print("=" * 80)
print()

subprocess.run(cmd)
