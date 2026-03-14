"""
启动 React 前端开发服务器（简化版）
直接使用 npm 命令启动
"""

import sys
import subprocess
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
frontend_dir = project_root / "web" / "frontend"

print("=" * 80)
print("🌐 启动医疗 Agent Web 前端")
print("=" * 80)
print()
print(f"前端目录：{frontend_dir}")
print()
print("访问地址：http://localhost:3000")
print()
print("提示：按 Ctrl+C 停止服务")
print("=" * 80)
print()

# 检查 node_modules
node_modules = frontend_dir / "node_modules"
if not node_modules.exists():
    print("⚠️  node_modules 不存在，正在安装依赖...")
    print()
    try:
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
    except Exception as e:
        print(f"❌ 依赖安装失败：{e}")
        print("请手动运行：cd web/frontend && npm install")
        sys.exit(1)
    print()

# 启动 React 开发服务器
print("正在启动 React 开发服务器...")
print()

try:
    # 使用 subprocess 启动，更好地控制进程
    process = subprocess.Popen(
        ["npm", "start"],
        cwd=frontend_dir,
        shell=True,
    )
    process.wait()
except KeyboardInterrupt:
    print("\n👋 Web 前端已停止")
    process.terminate()
except Exception as e:
    print(f"❌ 启动失败：{e}")
    sys.exit(1)
