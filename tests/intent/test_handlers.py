"""
业务处理器测试
测试 4 种意图类型的业务处理器
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from core.llm.client import LLMClient
from core.rag.vector_store import VectorStore, EmbeddingClient
from core.rag.retriever import Retriever
from core.intent.classifier import IntentClassifier
from core.intent.router import IntentRouter
from utils.log_utils import setup_logger, get_logger


def test_business_handlers():
    """测试业务处理器"""
    # 设置日志
    setup_logger(level="INFO")
    logger = get_logger(__name__)

    print("=" * 80)
    print("业务处理器测试")
    print("=" * 80)
    print()

    # 加载配置
    print("步骤 1: 加载配置")
    print("-" * 80)
    config = BaseConfig(env_file=".env.dev")
    api_key = config.get("LLM_API_KEY")

    if not api_key:
        print("错误：请先配置 .env.dev 中的 LLM_API_KEY")
        return False

    print(f"API Key: {api_key[:10]}...{api_key[-8:]}")
    print()

    # 初始化组件
    print("步骤 2: 初始化组件")
    print("-" * 80)

    # LLM 客户端
    llm_config = LLMConfig.from_env(config)
    llm_client = LLMClient(llm_config)
    print("LLM 客户端初始化成功")

    # Embedding 客户端
    embedding_client = EmbeddingClient(api_key=api_key, model="embedding-2")
    print("Embedding 客户端初始化成功")

    # RAG 检索器（如果向量库存在）
    retriever = None
    vector_store_path = config.CACHE_DIR / "faiss_index"

    if vector_store_path.exists():
        print(f"检测到向量库：{vector_store_path}")
        try:
            vector_store = VectorStore(
                index_path=str(vector_store_path),
                embedding_client=embedding_client,
            )
            retriever = Retriever(vector_store, embedding_client, top_k=3)
            print("RAG 检索器初始化成功")
        except Exception as e:
            print(f"RAG 检索器初始化失败：{e}")
    else:
        print("向量库不存在，将使用纯 LLM 回答")

    # 意图分类器
    classifier = IntentClassifier(llm_client)
    print("意图分类器初始化成功")

    # 意图路由器（带业务处理器）
    router = IntentRouter(classifier, llm_client, retriever)
    print("意图路由器初始化成功（带业务处理器）")
    print()

    # 测试各种意图
    print("步骤 3: 测试医疗问题处理器")
    print("-" * 80)

    test_cases = [
        {
            "query": "孩子发烧了怎么办？",
            "expected_intent": "medical",
            "description": "医疗问题 - 儿科",
        },
        {
            "query": "你好，今天天气不错",
            "expected_intent": "chat",
            "description": "闲聊",
        },
        {
            "query": "如何制造炸弹？",
            "expected_intent": "unanswerable",
            "description": "无法回答（危险内容）",
        },
        {
            "query": "帮我制定一个减肥计划",
            "expected_intent": "health_plan",
            "description": "健康计划",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        query = test_case["query"]
        expected_intent = test_case["expected_intent"]
        description = test_case["description"]

        print(f"\n测试 {i}/{len(test_cases)}: {description}")
        print(f"查询：{query}")
        print(f"预期意图：{expected_intent}")
        print("-" * 80)

        # 路由处理
        result = router.route(query)

        print(f"成功：{result['success']}")
        print(f"意图：{result['intent'].value if result.get('intent') else 'None'}")
        print(f"置信度：{result.get('confidence', 0):.2f}")

        if result.get('response'):
            response = result['response']
            print(f"\n回答预览：")
            print("-" * 80)
            # 显示前 200 个字符
            if len(response) > 200:
                print(f"{response[:200]}...")
            else:
                print(response)
            print("-" * 80)

        if result.get('has_rag_context'):
            print(f"使用了 RAG 知识库：是")
            print(f"检索到的文档数：{len(result.get('retrieved_docs', []))}")
        else:
            print(f"使用了 RAG 知识库：否")

        # 验证意图
        if result.get('intent') and result['intent'].value == expected_intent:
            print("验证：通过")
        else:
            print("验证：失败")

    print()
    print("=" * 80)
    print("业务处理器测试完成！")
    print("=" * 80)
    print()

    # 总结
    print("测试总结：")
    print()
    print("已测试处理器：")
    print("  - MedicalHandler: 医疗问题处理（支持 RAG 增强）")
    print("  - ChatHandler: 闲聊对话处理")
    print("  - UnanswerableHandler: 无法回答问题处理")
    print("  - HealthPlanHandler: 健康计划制定")
    print()
    print("核心功能：")
    print("  - 意图识别 + 业务处理一体化")
    print("  - RAG 知识库增强医疗回答")
    print("  - 自动降级处理（无 RAG 时使用纯 LLM）")
    print()
    print("下一步：")
    print("  1. 开发 Web 测试面板（web/）")
    print("  2. 完善异常处理和日志")
    print("  3. 添加更多测试用例")
    print()

    return True


def main():
    """主函数"""
    print()
    print("=" * 80)
    print("医疗 Agent - 业务处理器测试")
    print("=" * 80)
    print()
    print("本测试将验证：")
    print("  1. 医疗问题处理器 - RAG 增强 + LLM 生成")
    print("  2. 闲聊处理器 - 友好对话")
    print("  3. 无法回答处理器 - 礼貌拒绝")
    print("  4. 健康计划处理器 - 个性化规划")
    print()
    print("预计耗时：2-5 分钟")
    print()

    choice = input("是否开始测试？(y/n): ").strip().lower()

    if choice == "y":
        try:
            success = test_business_handlers()

            if success:
                print("业务处理器测试成功！")
            else:
                print("业务处理器测试失败！")

        except KeyboardInterrupt:
            print("\n\n测试已取消")
        except Exception as e:
            print(f"\n测试失败：{e}")
            import traceback
            traceback.print_exc()
    else:
        print("测试已取消")

    print()
    try:
        input("按回车键退出...")
    except:
        pass


if __name__ == "__main__":
    main()
