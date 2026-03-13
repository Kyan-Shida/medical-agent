"""
连接测试脚本
测试 API 连接和配置
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from core.llm.client import LLMClient
from utils.log_utils import setup_logger


def test_api_connection():
    """测试 API 连接"""
    print("=" * 80)
    print("API 连接测试")
    print("=" * 80)

    # 加载配置
    config = BaseConfig(env_file=".env.dev")
    api_key = config.get("LLM_API_KEY")

    if not api_key:
        print("❌ 错误：未找到 API Key")
        print("请检查 .env.dev 文件中的 LLM_API_KEY 配置")
        return False

    print(f"✅ API Key: {api_key[:10]}...{api_key[-8:]}")

    # 初始化 LLM 客户端
    llm_config = LLMConfig.from_env(config)
    llm_client = LLMClient(llm_config)

    # 测试连接
    print("\n正在测试 API 连接...")
    try:
        response = llm_client.simple_chat("你好", system_prompt="你是一个友好的助手")
        print(f"✅ API 连接成功")
        print(f"AI 回复：{response[:100]}...")
        return True
    except Exception as e:
        print(f"❌ API 连接失败：{e}")
        return False


def test_rag_connection():
    """测试 RAG 组件"""
    print("\n" + "=" * 80)
    print("RAG 组件测试")
    print("=" * 80)

    config = BaseConfig(env_file=".env.dev")
    api_key = config.get("LLM_API_KEY")

    # 检查向量库
    vector_store_path = config.CACHE_DIR / "faiss_index"

    if vector_store_path.exists():
        print(f"✅ 向量库存在：{vector_store_path}")

        try:
            from core.rag.vector_store import VectorStore, EmbeddingClient
            from core.rag.retriever import Retriever

            # 初始化向量库
            embedding_client = EmbeddingClient(api_key=api_key, model="embedding-2")
            vector_store = VectorStore(
                index_path=str(vector_store_path),
                embedding_client=embedding_client,
            )

            retriever = Retriever(vector_store, embedding_client, top_k=3)

            # 测试检索
            query = "儿童发烧"
            results = retriever.retrieve(query)

            print(f"✅ RAG 检索测试成功")
            print(f"检索到 {len(results)} 个相关文档")

            return True
        except Exception as e:
            print(f"⚠️ RAG 组件初始化失败：{e}")
            return False
    else:
        print(f"⚠️ 向量库不存在：{vector_store_path}")
        print("提示：运行 python scripts/build_knowledge_base.py 构建向量库")
        return False


def test_intent_recognition():
    """测试意图识别"""
    print("\n" + "=" * 80)
    print("意图识别测试")
    print("=" * 80)

    config = BaseConfig(env_file=".env.dev")
    llm_config = LLMConfig.from_env(config)
    llm_client = LLMClient(llm_config)

    from core.intent.classifier import IntentClassifier

    classifier = IntentClassifier(llm_client)

    # 测试用例
    test_cases = [
        ("孩子发烧了怎么办？", "medical"),
        ("你好", "chat"),
        ("帮我制定减肥计划", "health_plan"),
    ]

    success_count = 0
    for query, expected_intent in test_cases:
        result = classifier.classify(query)
        actual_intent = result["intent"].value

        if actual_intent == expected_intent:
            print(f"✅ {query} -> {actual_intent}")
            success_count += 1
        else:
            print(f"❌ {query} -> {actual_intent} (预期：{expected_intent})")

    print(f"\n测试通过率：{success_count}/{len(test_cases)}")
    return success_count == len(test_cases)


def main():
    """主函数"""
    setup_logger(level="INFO")

    print("\n医疗 Agent 连接测试\n")

    # 测试 API 连接
    api_ok = test_api_connection()

    # 测试 RAG 组件
    rag_ok = test_rag_connection() if api_ok else False

    # 测试意图识别
    intent_ok = test_intent_recognition() if api_ok else False

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"API 连接：{'✅ 正常' if api_ok else '❌ 失败'}")
    print(f"RAG 组件：{'✅ 正常' if rag_ok else '⚠️ 未测试/失败'}")
    print(f"意图识别：{'✅ 正常' if intent_ok else '⚠️ 未测试/失败'}")

    if api_ok and intent_ok:
        print("\n✅ 系统运行正常，可以开始使用")
        print("\n启动 Web 面板：python web/run_app.py")
        print("命令行聊天：python scripts/chat.py")
    else:
        print("\n⚠️ 部分组件异常，请检查配置")

    print("=" * 80)
    print()


if __name__ == "__main__":
    main()
