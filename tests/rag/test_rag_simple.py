"""
RAG 模块快速测试脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent  # tests/rag/ -> tests/ -> medical/
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.rag_config import RAGConfig
from core.rag.document_loader import DocumentLoader
from core.rag.text_splitter import TextSplitter
from core.rag.vector_store import VectorStore, EmbeddingClient
from core.rag.retriever import Retriever
from utils.log_utils import setup_logger, get_logger


def test_rag_flow():
    """测试完整的 RAG 流程"""
    # 设置日志
    setup_logger(level="INFO")
    logger = get_logger(__name__)

    print("=" * 60)
    print("RAG 模块测试")
    print("=" * 60)
    print()

    # 加载配置
    config = BaseConfig(env_file=".env.dev")
    api_key = config.get("LLM_API_KEY")

    if not api_key or api_key == "your_dev_api_key":
        print("❌ 错误：请先配置 .env.dev 中的 LLM_API_KEY")
        return

    print(f"✅ 配置加载成功")
    print(f"API Key: {api_key[:10]}...")
    print()

    # 1. 文档加载
    print("步骤 1: 文档加载")
    print("-" * 60)
    loader = DocumentLoader()

    # 创建测试文档
    test_text = """
    儿童发烧处理指南
    
    儿童发烧是常见症状，家长应该保持冷静。
    
    【家庭护理】
    1. 测量体温，确认发烧程度
    2. 让孩子多休息，多喝水
    3. 适当减少衣物，保持室内通风
    4. 体温超过 38.5℃可考虑使用退烧药
    
    【退烧药使用】
    - 对乙酰氨基酚（泰诺林）：适用于 3 个月以上
    - 布洛芬（美林）：适用于 6 个月以上
    - 按照体重计算剂量
    - 两种药不建议交替使用
    
    【何时就医】
    - 3 个月以下婴儿发烧
    - 持续高烧不退（超过 39℃）
    - 出现抽搐、呼吸困难
    - 精神状态差、嗜睡
    """

    doc = loader.load_from_text(test_text, source="儿童医疗指南")
    print(f"✅ 文档加载成功：{len(doc.content)} 字符")
    print()

    # 2. 文本分割
    print("步骤 2: 文本分割")
    print("-" * 60)
    splitter = TextSplitter(chunk_size=200, chunk_overlap=50)

    documents = [{"content": doc.content, "metadata": doc.metadata}]
    split_docs = splitter.split_documents(documents)

    print(f"✅ 文本分割完成：{len(split_docs)} 个文本块")
    for i, chunk in enumerate(split_docs[:3], 1):
        print(f"   块{i}: {len(chunk['content'])} 字符")
    print()

    # 3. 创建向量库
    print("步骤 3: 创建向量库")
    print("-" * 60)
    embedding_client = EmbeddingClient(api_key=api_key, model="embedding-2")
    vector_store = VectorStore(
        index_path="cache/faiss_index_test",
        embedding_client=embedding_client,
    )

    print("正在获取向量...")
    doc_ids = vector_store.add_documents(split_docs)
    print(f"✅ 向量库创建成功：{len(doc_ids)} 个文档")
    print()

    # 4. 检索测试
    print("步骤 4: 检索测试")
    print("-" * 60)

    retriever = Retriever(
        vector_store=vector_store,
        embedding_client=embedding_client,
        top_k=2,
    )

    # 测试查询
    test_queries = [
        "儿童发烧怎么办？",
        "退烧药怎么使用？",
        "什么时候需要去医院？",
    ]

    for query in test_queries:
        print(f"\n查询：{query}")
        print("-" * 40)

        results = retriever.retrieve(query, top_k=2)

        if results:
            for i, (doc, score) in enumerate(results, 1):
                print(f"  结果{i}: (相似度：{score:.3f})")
                print(f"  {doc.content[:80]}...")
        else:
            print("  无结果")

    print()
    print("=" * 60)
    print("✅ RAG 模块测试完成！")
    print("=" * 60)
    print()

    # 显示统计信息
    stats = retriever.get_stats()
    print("统计信息：")
    print(f"  - 文档数量：{stats['vector_store']['document_count']}")
    print(f"  - 向量维度：{stats['vector_store']['dimension']}")
    print(f"  - Top-K: {stats['top_k']}")
    print()


def main():
    """主函数"""
    print()
    print("=" * 60)
    print("医疗 Agent - RAG 模块测试")
    print("=" * 60)
    print()
    print("本测试将验证：")
    print("1. 文档加载功能")
    print("2. 文本分割功能")
    print("3. Embedding 向量化（使用智谱 AI API）")
    print("4. FAISS 向量存储")
    print("5. 相似度检索")
    print()
    print("注意：需要配置有效的 LLM_API_KEY")
    print()

    choice = input("是否开始测试？(y/n): ").strip().lower()

    if choice == "y":
        try:
            test_rag_flow()
        except KeyboardInterrupt:
            print("\n\n测试中断")
        except Exception as e:
            print(f"\n❌ 测试失败：{e}")
            import traceback

            traceback.print_exc()
    else:
        print("测试已取消")


if __name__ == "__main__":
    main()
