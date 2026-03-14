"""
启动 React 前端开发服务器
"""

import sys
import subprocess
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent

print("=" * 80)
print("🌐 启动医疗 Agent Web 前端")
print("=" * 80)
print()

frontend_dir = project_root / "web" / "frontend"

if not frontend_dir.exists():
    print("❌ 错误：前端目录不存在")
    sys.exit(1)

print(f"前端目录：{frontend_dir}")
print()
print("正在启动 React 开发服务器...")
print()
print("访问地址：http://localhost:3000")
print()
print("提示：按 Ctrl+C 停止服务")
print("=" * 80)

# 安装依赖（如果需要）
try:
    subprocess.run(
        ["npm", "install"],
        cwd=frontend_dir,
        check=True,
    )
except (subprocess.CalledProcessError, FileNotFoundError) as e:
    print(f"⚠️ npm install 失败：{e}")
    print("提示：请确保已安装 Node.js 和 npm")

# 启动开发服务器
try:
    subprocess.run(
        ["npm", "start"],
        cwd=frontend_dir,
        check=True,
    )
except KeyboardInterrupt:
    print("\n👋 Web 前端已停止")
except subprocess.CalledProcessError as e:
    print(f"❌ 启动失败：{e}")
    sys.exit(1)
except FileNotFoundError:
    print("❌ 错误：找不到 npm 命令")
    print("提示：请安装 Node.js (https://nodejs.org/)")
    sys.exit(1)
