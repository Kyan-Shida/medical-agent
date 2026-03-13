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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="医疗 Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 测试 LLM 连接
  python main.py --chat             # 交互式聊天
  python main.py --web              # 启动 Web 面板
  python main.py --test             # 运行测试
  python main.py --env .env.prod    # 使用生产环境配置
        """,
    )
    parser.add_argument(
        "--env",
        type=str,
        default=".env.dev",
        help="环境配置文件 (默认：.env.dev)",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="交互式聊天模式",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="运行测试",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="启动 Web 面板",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认：INFO)",
    )

    args = parser.parse_args()

    # 设置日志
    setup_logger(level=args.log_level)
    logger = get_logger(__name__)

    logger.info("=" * 80)
    logger.info("🏥 医疗 Agent 启动中...")
    logger.info("=" * 80)

    # 加载配置
    config = BaseConfig(env_file=args.env)
    logger.info(f"✅ 配置加载成功：{args.env}")
    logger.info(f"📊 日志级别：{args.log_level}")

    if args.test:
        # 运行测试
        run_tests(config)
    elif args.chat:
        # 交互式聊天
        interactive_chat(config)
    elif args.web:
        # 启动 Web 面板
        start_web(config)
    else:
        # 默认模式：测试 LLM 连接
        test_llm_connection(config)


@handle_exception(default_message="测试运行失败")
def run_tests(config):
    """运行测试"""
    import pytest

    logger = get_logger(__name__)
    logger.info("=" * 80)
    logger.info("🧪 开始运行测试...")
    logger.info("=" * 80)

    pytest.main(["-v", "tests/"])


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
