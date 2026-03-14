"""
医疗 Agent 主入口
提供命令行界面，支持测试、聊天、Web 面板等多种模式
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from core.llm.client import LLMClient
from core.intent.classifier import IntentClassifier
from core.intent.router import IntentRouter
from utils.log_utils import setup_logger, get_logger
from utils.exception_handler import handle_exception
from utils.log_enhanced import track_performance


def show_menu():
    """显示交互式菜单"""
    print("=" * 80)
    print("🏥 医疗 Agent - 主菜单")
    print("=" * 80)
    print()
    print("请选择功能：")
    print()
    print("  1. 测试 LLM 连接")
    print("  2. 一键启动 Web 前端（API + React）⭐ 推荐")
    print("  3. 启动产品经理数据面板")
    print("  4. 交互式聊天")
    print("  5. 启动旧版 Web 面板（Streamlit）")
    print("  6. 运行测试")
    print("  0. 退出")
    print()
    print("=" * 80)
    return input("请输入选项 (0-6): ").strip()


def main():
    """主函数"""
    # 设置日志
    setup_logger(level="INFO")
    logger = get_logger(__name__)

    # 加载配置
    config = BaseConfig(env_file=".env.dev")
    logger.info(f"✅ 配置加载成功：.env.dev")

    while True:
        choice = show_menu()
        print()

        if choice == "1":
            # 测试 LLM 连接
            test_llm_connection(config)
        elif choice == "2":
            # 一键启动 Web 前端
            start_frontend(config)
        elif choice == "3":
            # 启动产品经理数据面板
            start_metrics(config)
        elif choice == "4":
            # 交互式聊天
            interactive_chat(config)
        elif choice == "5":
            # 启动旧版 Web 面板
            start_web(config)
        elif choice == "6":
            # 运行测试
            run_tests(config)
        elif choice == "0":
            # 退出
            logger.info("=" * 80)
            logger.info("👋 再见！")
            logger.info("=" * 80)
            sys.exit(0)
        else:
            print("❌ 无效的选项，请重新选择")
            print()


@handle_exception(default_message="一键启动 Web 前端失败")
def start_frontend(config):
    """
    一键启动 Web 前端
    同时启动 API 服务和 React 前端
    """
    import subprocess
    import time
    import sys

    logger = get_logger(__name__)
    logger.info("=" * 80)
    logger.info("🚀 一键启动 Web 前端")
    logger.info("=" * 80)
    logger.info("")
    logger.info("[1/2] 正在启动 API 服务...")

    # 启动 API 服务
    api_process = subprocess.Popen(
        [sys.executable, "web/run_api.py"],
        cwd=project_root,
    )
    logger.info("      ✅ API 服务已启动")
    logger.info("")

    # 等待 3 秒
    time.sleep(3)

    logger.info("[2/2] 正在启动前端服务...")

    # 启动前端服务
    frontend_process = subprocess.Popen(
        [sys.executable, "web/start_frontend.py"],
        cwd=project_root,
    )
    logger.info("      ✅ 前端服务已启动")
    logger.info("")

    logger.info("=" * 80)
    logger.info("🎉 启动完成！")
    logger.info("=" * 80)
    logger.info("")
    logger.info("访问地址:")
    logger.info("  🌐 Web 前端：http://localhost:3000")
    logger.info("  📡 API 服务：http://localhost:8000")
    logger.info("  📖 API 文档：http://localhost:8000/docs")
    logger.info("")
    logger.info("提示:")
    logger.info("  - 按 Ctrl+C 可停止所有服务")
    logger.info("  - 关闭窗口可完全退出")
    logger.info("")

    # 等待进程结束
    try:
        api_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        logger.info("\n👋 服务已停止")
        sys.exit(0)


@handle_exception(default_message="启动数据面板失败")
def start_metrics(config):
    """
    启动产品经理数据面板
    基于 Streamlit 实现
    """
    import subprocess
    import sys
    import os

    logger = get_logger(__name__)
    
    # 设置环境变量
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    
    # 构建命令
    app_path = project_root / "web" / "metrics_dashboard.py"
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port", "8502",
        "--server.address", "localhost",
        "--browser.serverAddress", "localhost",
    ]
    
    logger.info("=" * 80)
    logger.info("📊 产品经理数据面板")
    logger.info("=" * 80)
    logger.info("")
    logger.info("正在启动数据面板服务...")
    logger.info("")
    logger.info("访问地址：http://localhost:8502")
    logger.info("")
    logger.info("提示：按 Ctrl+C 停止服务")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        logger.info("\n👋 数据面板已停止")
        sys.exit(0)


@handle_exception(default_message="测试运行失败")
def run_tests(config):
    """运行测试"""
    import subprocess
    import sys

    logger = get_logger(__name__)
    logger.info("=" * 80)
    logger.info("🧪 开始运行测试...")
    logger.info("=" * 80)
    logger.info("")

    # 使用 subprocess 运行 pytest，确保路径正确
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        logger.error(f"❌ 测试目录不存在：{tests_dir}")
        return

    logger.info(f"测试目录：{tests_dir}")
    logger.info("")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", str(tests_dir)],
            cwd=project_root,
        )
        logger.info("")
        logger.info("=" * 80)
        if result.returncode == 0:
            logger.info("✅ 所有测试通过！")
        else:
            logger.warning(f"⚠️  部分测试失败，退出码：{result.returncode}")
        logger.info("=" * 80)
    except Exception as e:
        logger.error(f"❌ 测试运行失败：{e}")


@handle_exception(default_message="启动 Web 面板失败")
@track_performance("启动 Web 面板")
def start_web(config):
    """启动 Web 面板"""
    import subprocess

    logger = get_logger(__name__)
    logger.info("=" * 80)
    logger.info("🌐 启动 Web 面板...")
    logger.info("=" * 80)

    web_port = config.get_int("WEB_PORT", 8501)
    web_address = config.get("WEB_ADDRESS", "localhost")

    logger.info(f"访问地址：http://{web_address}:{web_port}")
    logger.info("按 Ctrl+C 停止服务")
    logger.info("-" * 80)

    subprocess.run(
        [
            "streamlit",
            "run",
            "web/app.py",
            "--server.port",
            str(web_port),
            "--server.address",
            web_address,
        ],
        cwd=project_root,
    )


@handle_exception(default_message="LLM 连接测试失败")
@track_performance("LLM 连接测试")
def test_llm_connection(config):
    """测试 LLM 连接"""
    logger = get_logger(__name__)
    logger.info("=" * 80)
    logger.info("🔍 测试 LLM 连接...")
    logger.info("=" * 80)

    # 加载 LLM 配置
    llm_config = LLMConfig.from_env(config)

    # 检查配置
    if not llm_config.validate():
        logger.error("❌ LLM 配置无效，请检查环境变量")
        logger.info(f"API Key: {'已设置' if llm_config.api_key else '未设置'}")
        logger.info(f"Base URL: {llm_config.base_url}")
        logger.info(f"Model: {llm_config.model}")
        return

    logger.info("✅ LLM 配置验证通过")

    # 创建客户端
    client = LLMClient(llm_config)
    logger.info("✅ LLM 客户端创建成功")

    # 测试连接
    logger.info("测试 API 连接...")
    if client.test_connection():
        logger.info("✅ API 连接测试通过")

        # 简单测试
        logger.info("发送测试消息...")
        response = client.simple_chat("你好，请用一句话介绍你自己")
        logger.info(f"✅ AI 回复：{response}")
    else:
        logger.error("❌ API 连接测试失败")

    logger.info("=" * 80)
    logger.info("💡 提示：使用 --chat 进入交互式聊天模式")
    logger.info("=" * 80)


@handle_exception(default_message="聊天过程出错")
def interactive_chat(config):
    """
    交互式聊天模式
    支持多轮对话，显示意图识别和 RAG 检索结果
    """
    logger = get_logger(__name__)
    logger.info("=" * 80)
    logger.info("💬 进入交互式聊天模式")
    logger.info("=" * 80)
    logger.info("提示：")
    logger.info("  - 输入问题后按回车发送")
    logger.info("  - 输入 'quit' 或 'exit' 退出")
    logger.info("  - 输入 'clear' 清屏")
    logger.info("=" * 80)

    # 初始化组件
    llm_config = LLMConfig.from_env(config)
    llm_client = LLMClient(llm_config)
    classifier = IntentClassifier(llm_client)

    # 尝试初始化 RAG 检索器
    retriever = None
    vector_store_path = config.CACHE_DIR / "faiss_index"
    if vector_store_path.exists():
        try:
            from core.rag.vector_store import VectorStore, EmbeddingClient
            from core.rag.retriever import Retriever

            api_key = config.get("LLM_API_KEY")
            embedding_client = EmbeddingClient(api_key=api_key, model="embedding-2")
            vector_store = VectorStore(
                index_path=str(vector_store_path),
                embedding_client=embedding_client,
            )
            retriever = Retriever(vector_store, embedding_client, top_k=3)
            logger.info("✅ RAG 检索器已加载")
        except Exception as e:
            logger.warning(f"⚠️ RAG 检索器加载失败：{e}")

    # 创建路由器
    router = IntentRouter(classifier, llm_client, retriever)
    logger.info("✅ 聊天系统就绪")
    logger.info("=" * 80)

    # 聊天循环
    conversation_count = 0

    while True:
        try:
            # 获取用户输入
            user_input = input("\n👤 你：").strip()

            if not user_input:
                continue

            # 检查退出命令
            if user_input.lower() in ["quit", "exit", "q"]:
                logger.info("=" * 80)
                logger.info(f"👋 聊天结束，共对话 {conversation_count} 轮")
                logger.info("=" * 80)
                break

            # 检查清屏命令
            if user_input.lower() == "clear":
                import os

                os.system("cls" if os.name == "nt" else "clear")
                logger.info("🧹 屏幕已清空")
                continue

            conversation_count += 1

            # 路由处理（包含意图识别和业务处理）
            logger.info("⏳ 思考中...")
            result = router.route(user_input)

            # 显示结果
            if result.get("success"):
                # 显示意图信息
                intent = result.get("intent")
                confidence = result.get("confidence", 0)
                logger.info(f"🎯 意图：{intent.value if intent else 'unknown'} ({confidence:.1%})")

                # 显示 RAG 检索结果
                if result.get("has_rag_context"):
                    docs = result.get("retrieved_docs", [])
                    logger.info(f"📚 RAG 检索：{len(docs)} 个相关文档")

                # 显示 AI 回答
                logger.info("-" * 80)
                logger.info(f"🤖 AI: {result.get('response', '')}")
                logger.info("-" * 80)
            else:
                logger.error(f"❌ 处理失败：{result.get('message', '未知错误')}")

        except KeyboardInterrupt:
            logger.info("\n\n⚠️  检测到 Ctrl+C，退出聊天")
            logger.info("=" * 80)
            break
        except Exception as e:
            logger.error(f"❌ 聊天出错：{e}")
            logger.debug("详细错误:", exc_info=True)


if __name__ == "__main__":
    main()
