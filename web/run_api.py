"""
启动 API 服务
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("🚀 启动医疗 Agent API 服务")
print("=" * 80)
print()
print("正在启动 API 服务...")
print()

# 运行 API 应用
from api.app import main

if __name__ == "__main__":
    main()
