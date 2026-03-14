"""
验证 Web 前端安装和配置
"""

import sys
import subprocess
from pathlib import Path

def print_header(text):
    print("=" * 80)
    print(f"  {text}")
    print("=" * 80)
    print()

def check_python_deps():
    """检查 Python 依赖"""
    print_header("步骤 1: 检查 Python 依赖")
    
    deps = {
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "streamlit": "Streamlit",
    }
    
    all_ok = True
    for package, name in deps.items():
        try:
            __import__(package)
            print(f"  ✅ {name}: 已安装")
        except ImportError:
            print(f"  ❌ {name}: 未安装")
            all_ok = False
    
    if not all_ok:
        print("\n  提示：运行 'pip install -r requirements.txt' 安装依赖")
    
    print()
    return all_ok

def check_node():
    """检查 Node.js"""
    print_header("步骤 2: 检查 Node.js")
    
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        version = result.stdout.strip()
        print(f"  ✅ Node.js: {version}")
        
        # 检查 npm
        result = subprocess.run(
            ["npm", "--version"],
            capture_output=True,
            text=True,
            check=True,
        )
        version = result.stdout.strip()
        print(f"  ✅ npm: {version}")
        
        print()
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ❌ Node.js 或 npm 未安装")
        print("\n  提示：访问 https://nodejs.org/ 安装 Node.js")
        print()
        return False

def check_frontend_deps():
    """检查前端依赖"""
    print_header("步骤 3: 检查前端依赖")
    
    frontend_dir = Path(__file__).parent / "web" / "frontend"
    node_modules = frontend_dir / "node_modules"
    
    if node_modules.exists():
        print(f"  ✅ node_modules: 已安装")
        
        # 检查关键包
        key_packages = ["react", "axios", "framer-motion"]
        for package in key_packages:
            package_dir = node_modules / package
            if package_dir.exists():
                print(f"    ✅ {package}: 已安装")
            else:
                print(f"    ❌ {package}: 未安装")
    else:
        print(f"  ❌ node_modules: 未安装")
        print("\n  提示：运行 'npm install' 安装前端依赖")
    
    print()

def check_env_files():
    """检查环境配置文件"""
    print_header("步骤 4: 检查环境配置文件")
    
    root_dir = Path(__file__).parent
    
    # 检查 .env.dev
    env_dev = root_dir / ".env.dev"
    if env_dev.exists():
        print(f"  ✅ .env.dev: 存在")
        
        # 检查 API Key
        content = env_dev.read_text(encoding="utf-8")
        if "LLM_API_KEY=" in content and "your_zhipu_api_key_here" not in content:
            print(f"    ✅ LLM_API_KEY: 已配置")
        else:
            print(f"    ⚠️  LLM_API_KEY: 未配置或为默认值")
    else:
        print(f"  ❌ .env.dev: 不存在")
        print(f"    提示：复制 .env.example 并配置")
    
    # 检查前端 .env
    frontend_env = root_dir / "web" / "frontend" / ".env"
    if frontend_env.exists():
        print(f"  ✅ web/frontend/.env: 存在")
    else:
        print(f"  ❌ web/frontend/.env: 不存在")
        print(f"    提示：复制 web/frontend/.env.example 并配置")
    
    print()

def check_api():
    """检查 API 服务"""
    print_header("步骤 5: 检查 API 服务")
    
    import requests
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ API 服务：运行中")
            print(f"    状态：{data.get('status', 'unknown')}")
            print(f"    LLM: {'✅' if data.get('llm') else '❌'}")
            print(f"    RAG: {'✅' if data.get('rag') else '❌'}")
            print(f"    意图识别：{'✅' if data.get('intent_classifier') else '❌'}")
        else:
            print(f"  ❌ API 服务：响应异常")
    except requests.exceptions.ConnectionError:
        print(f"  ❌ API 服务：未运行")
        print(f"    提示：运行 'python web/run_api.py' 启动 API")
    except Exception as e:
        print(f"  ❌ API 服务：检查失败 - {e}")
    
    print()

def check_frontend():
    """检查前端服务"""
    print_header("步骤 6: 检查前端服务")
    
    import requests
    
    try:
        response = requests.get("http://localhost:3000", timeout=2)
        if response.status_code == 200:
            print(f"  ✅ 前端服务：运行中")
        else:
            print(f"  ⚠️  前端服务：响应异常")
    except requests.exceptions.ConnectionError:
        print(f"  ❌ 前端服务：未运行")
        print(f"    提示：运行 'python web/run_frontend.py' 启动前端")
    except Exception as e:
        print(f"  ❌ 前端服务：检查失败 - {e}")
    
    print()

def main():
    """主函数"""
    print_header("🔍 医疗 Agent Web 前端验证工具")
    
    # 执行检查
    python_ok = check_python_deps()
    node_ok = check_node()
    check_frontend_deps()
    check_env_files()
    
    # 检查服务状态（可选）
    print("是否检查服务运行状态？(y/n): ", end="")
    try:
        choice = input().strip().lower()
        if choice == 'y':
            check_api()
            check_frontend()
    except:
        pass
    
    # 总结
    print_header("✅ 检查完成")
    
    if python_ok and node_ok:
        print("  🎉 所有依赖已就绪！")
        print()
        print("  启动方式：")
        print("    1. 双击 start.bat")
        print("    2. 选择 1: 工业级 Web 前端")
        print()
        print("  访问地址：")
        print("    🌐 Web 前端：http://localhost:3000")
        print("    📡 API 服务：http://localhost:8000")
        print("    📖 API 文档：http://localhost:8000/docs")
    else:
        print("  ⚠️  部分依赖未安装，请先完成安装")
    
    print()
    print_header("")

if __name__ == "__main__":
    main()
