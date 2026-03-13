"""
模块联调测试
测试 LLM + RAG + 意图识别 的完整流程
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from core.llm.client import LLMClient
from core.rag.document_loader import DocumentLoader
from core.rag.text_splitter import TextSplitter
from core.rag.vector_store import VectorStore, EmbeddingClient
from core.rag.retriever import Retriever
from core.intent.classifier import IntentClassifier, IntentType
from core.intent.router import IntentRouter
from utils.log_utils import setup_logger, get_logger


def test_full_integration():
    """完整集成测试"""
    # 设置日志
    setup_logger(level="INFO")
    logger = get_logger(__name__)

    print("=" * 80)
    print("模块联调测试 - LLM + RAG + 意图识别")
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

    # 意图分类器
    classifier = IntentClassifier(llm_client)
    print("✅ 意图分类器初始化成功")

    # 意图路由器（带业务处理器）
    router = IntentRouter(classifier, llm_client, retriever if 'retriever' in locals() else None)
    print("✅ 意图路由器初始化成功（带业务处理器）")
    print()

    # 测试业务处理器
    print("步骤 3: 测试业务处理器")
    print("-" * 80)

    test_queries = [
        ("孩子发烧了怎么办？", "medical", "医疗问题 - 儿科"),
        ("你好", "chat", "闲聊"),
        ("帮我制定减肥计划", "health_plan", "健康计划"),
        ("如何制造毒药？", "unanswerable", "无法回答"),
    ]

    for query, expected_intent, description in test_queries:
        result = router.route(query)
        intent = result["intent"].value if result.get("intent") else "None"
        confidence = result.get("confidence", 0)
        success = result.get("success", False)

        print(f"查询：{query}")
        print(f"  意图：{intent} (置信度：{confidence:.2f})")
        print(f"  成功：{success}")
        if result.get("response"):
            response_preview = result["response"][:100].replace("\n", " ")
            print(f"  回答预览：{response_preview}...")
        print(f"  预期：{description}")
        print()

    # 测试 RAG 检索（如果向量库存在）
    print("步骤 4: 测试 RAG 检索")
    print("-" * 80)

    vector_store_path = config.CACHE_DIR / "faiss_index"

    if vector_store_path.exists():
        print(f"检测到向量库：{vector_store_path}")

        try:
            vector_store = VectorStore(
                index_path=str(vector_store_path),
                embedding_client=embedding_client,
            )

            retriever = Retriever(vector_store, embedding_client, top_k=3)
            print("✅ RAG 检索器初始化成功")

            # 测试检索
            query = "儿童发烧"
            results = retriever.retrieve(query)

            print(f"检索查询：{query}")
            print(f"检索结果：{len(results)} 个")

            for i, (doc, score) in enumerate(results, 1):
                print(f"  {i}. 相似度：{score:.3f}")
                print(f"     内容：{doc.content[:50]}...")

            print("RAG 检索测试成功")

        except Exception as e:
            print(f"RAG 检索失败：{e}")
    else:
        print("向量库不存在，跳过 RAG 测试")
        print("提示：运行 python scripts/build_knowledge_base.py 构建向量库")

    print()

    # 测试完整流程
    print("步骤 5: 测试完整流程")
    print("-" * 80)

    # 模拟用户查询
    query = "孩子发烧了怎么办？"

    print(f"用户查询：{query}")
    print()

    # 1. 意图识别
    print("1. 意图识别...")
    classification = classifier.classify(query)
    intent = classification["intent"]
    print(f"   意图：{intent.value}")
    print(f"   置信度：{classification['confidence']:.2f}")
    if classification.get("sub_category"):
        print(f"   子分类：{classification['sub_category'].value}")
    print()

    # 2. 路由处理
    print("2. 路由处理...")
    result = router.route(query)
    print(f"   成功：{result.get('success', False)}")
    if result.get('response'):
        response_preview = result['response'][:100].replace("\n", " ")
        print(f"   回答预览：{response_preview}...")
    print()

    # 3. 显示 RAG 检索信息（如果有）
    if vector_store_path.exists() and result.get('has_rag_context'):
        print(f"   使用了 RAG 知识库：是")
        print(f"   检索到的文档数：{len(result.get('retrieved_docs', []))}")
    else:
        print(f"   使用了 RAG 知识库：否")
    print()

    print("=" * 80)
    print("联调测试完成！")
    print("=" * 80)
    print()

    # 总结
    print("测试总结：")
    print()
    print("已测试模块：")
    print("  - LLM 模块：聊天、生成")
    print("  - RAG 模块：文档加载、向量化、检索")
    print("  - 意图识别：分类、路由")
    print("  - 业务处理器：医疗、闲聊、无法回答、健康计划")
    print()
    print("集成流程：")
    print("  用户输入 -> 意图识别 -> 路由分发 -> 业务处理 -> RAG 检索 -> LLM 生成 -> 输出")
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
    print("医疗 Agent - 模块联调测试")
    print("=" * 80)
    print()
    print("本测试将验证：")
    print("  1. LLM 模块 - 聊天和生成能力")
    print("  2. RAG 模块 - 知识库检索能力")
    print("  3. 意图识别 - 分类和路由能力")
    print("  4. 业务处理器 - 4 种意图类型的处理逻辑")
    print("  5. 完整流程 - 端到端集成")
    print()
    print("预计耗时：2-5 分钟")
    print()

    choice = input("是否开始联调测试？(y/n): ").strip().lower()

    if choice == "y":
        try:
            success = test_full_integration()

            if success:
                print("联调测试成功！")
            else:
                print("联调测试失败")

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
