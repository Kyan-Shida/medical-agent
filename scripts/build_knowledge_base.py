"""
知识库向量库预构建脚本
一次性构建，持久化使用，节省 Token

使用方法：
    python build_knowledge_base.py

说明：
    1. 只会消耗一次 Token（构建时）
    2. 后续使用直接从本地加载，不消耗 Token
    3. 查询时仅对查询文本进行 Embedding（少量 Token）
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from core.rag.document_loader import DocumentLoader
from core.rag.text_splitter import TextSplitter
from core.rag.vector_store import VectorStore, EmbeddingClient
from utils.log_utils import setup_logger, get_logger


def build_knowledge_base():
    """构建知识库向量库"""
    # 设置日志
    setup_logger(level="INFO")
    logger = get_logger(__name__)

    print("=" * 80)
    print("医疗 Agent - 知识库向量库构建工具")
    print("=" * 80)
    print()
    print(f"构建时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 加载配置
    print("步骤 1: 加载配置")
    print("-" * 80)
    config = BaseConfig(env_file=".env.dev")
    api_key = config.get("LLM_API_KEY")

    if not api_key or api_key == "your_dev_api_key":
        print("❌ 错误：请先在 .env.dev 中配置 LLM_API_KEY")
        return False

    print(f"✅ API Key: {api_key[:10]}...{api_key[-8:]}")
    print(f"✅ 知识库目录：{config.KNOWLEDGE_BASE_DIR}")
    print(f"✅ 缓存目录：{config.CACHE_DIR}")
    print()

    # 2. 检查知识库
    print("步骤 2: 检查知识库")
    print("-" * 80)
    knowledge_base = config.KNOWLEDGE_BASE_DIR

    if not knowledge_base.exists():
        print(f"❌ 知识库目录不存在：{knowledge_base}")
        print(f"💡 请创建目录并放入医疗文档（PDF/DOCX/TXT/MD）")
        knowledge_base.mkdir(parents=True, exist_ok=True)
        print(f"✅ 已创建目录：{knowledge_base}")
        return False

    # 统计文件
    files = list(knowledge_base.glob("*"))
    supported_files = [f for f in files if f.suffix.lower() in [".pdf", ".docx", ".txt", ".md"]]

    if not supported_files:
        print(f"⚠️  知识库目录为空：{knowledge_base}")
        print(f"💡 请放入医疗文档（PDF/DOCX/TXT/MD 格式）")
        return False

    print(f"✅ 找到 {len(supported_files)} 个文档")
    for file in supported_files:
        size_kb = file.stat().st_size / 1024
        print(f"   - {file.name} ({size_kb:.1f} KB)")
    print()

    # 3. 加载文档
    print("步骤 3: 加载文档")
    print("-" * 80)
    loader = DocumentLoader()

    try:
        docs = loader.load_directory(str(knowledge_base))
        total_chars = sum(len(doc.content) for doc in docs)
        print(f"✅ 加载成功：{len(docs)} 个文档，{total_chars:,} 字符")
    except Exception as e:
        print(f"❌ 加载失败：{e}")
        return False
    print()

    # 4. 文本分割
    print("步骤 4: 文本分割")
    print("-" * 80)
    splitter = TextSplitter(chunk_size=500, chunk_overlap=50)

    documents = [{"content": doc.content, "metadata": doc.metadata} for doc in docs]
    split_docs = splitter.split_documents(documents)

    print(f"✅ 分割完成：{len(split_docs)} 个文本块")
    if split_docs:
        print(f"   平均每个块：{sum(len(d['content']) for d in split_docs) // len(split_docs):.0f} 字符")
    print()

    # 5. 创建向量库
    print("步骤 5: 创建向量库（消耗 Token）")
    print("-" * 80)
    print("⏳ 正在调用 Embedding API，请稍候...")
    print()

    embedding_client = EmbeddingClient(api_key=api_key, model="embedding-2")
    vector_store = VectorStore(
        index_path=str(config.CACHE_DIR / "faiss_index"),
        embedding_client=embedding_client,
    )

    try:
        # 批量添加文档（节省 Token）
        doc_ids = vector_store.add_documents(split_docs)

        print(f"✅ 向量库构建成功！")
        print(f"   - 文档数量：{len(doc_ids)}")
        print(f"   - 保存位置：{config.CACHE_DIR / 'faiss_index'}")
        print()

    except Exception as e:
        print(f"❌ 构建失败：{e}")
        print()
        print("可能的原因：")
        print("  1. API Key 无效")
        print("  2. 网络连接问题")
        print("  3. Token 余额不足")
        return False

    # 6. 显示统计信息
    print("步骤 6: 统计信息")
    print("-" * 80)
    stats = vector_store.get_stats()

    print(f"向量库信息：")
    print(f"  - 文档总数：{stats['document_count']}")
    print(f"  - 向量维度：{stats['dimension']}")
    print(f"  - 索引类型：{stats['index_type']}")
    print(f"  - 存储路径：{stats['index_path']}")
    print()

    # 7. Token 消耗估算
    print("Token 消耗估算")
    print("-" * 80)
    estimated_tokens = total_chars // 2  # 粗略估算
    print(f"  - 本次构建：约 {estimated_tokens:,} token（一次性）")
    print(f"  - 后续查询：每次约 50-100 token")
    print(f"  - 缓存命中：0 token")
    print()
    print(f"💡 智谱 AI 免费额度：100 万 token/月")
    print(f"💡 本次构建约占免费额度的 {estimated_tokens / 10000:.1f}%")
    print()

    # 8. 使用说明
    print("后续使用说明")
    print("-" * 80)
    print("✅ 向量库已持久化保存，下次使用直接加载，不需要重新构建！")
    print()
    print("使用示例：")
    print("```python")
    print("from core.rag.vector_store import VectorStore, EmbeddingClient")
    print()
    print("# 直接加载已有向量库（不消耗 Token）")
    print("vector_store = VectorStore(")
    print("    index_path='cache/faiss_index',")
    print("    embedding_client=embedding_client,")
    print(")")
    print()
    print("# 查询时仅对查询文本进行 Embedding（少量 Token）")
    print("results = vector_store.similarity_search('儿童发烧怎么办？', top_k=3)")
    print("```")
    print()

    # 9. 完成
    print("=" * 80)
    print("✅ 知识库向量库构建完成！")
    print("=" * 80)
    print()
    print("下一步：")
    print("  1. 测试检索：python tests/test_rag_simple.py")
    print("  2. 结合 LLM：参考 docs/RAG 快速开始.md")
    print("  3. 添加新文档：重新运行本脚本（增量更新）")
    print()

    return True


def main():
    """主函数"""
    print()
    print("=" * 80)
    print("欢迎使用医疗 Agent 知识库构建工具")
    print("=" * 80)
    print()
    print("本工具将：")
    print("  1. 加载 knowledge_base/ 目录下的所有文档")
    print("  2. 分割文本为合适大小的块")
    print("  3. 调用智谱 AI Embedding API 进行向量化")
    print("  4. 保存到 cache/faiss_index/（持久化）")
    print()
    print("⏰ 预计耗时：1-5 分钟（取决于文档数量）")
    print("💰 Token 消耗：一次性，后续使用不消耗")
    print()

    choice = input("是否开始构建？(y/n): ").strip().lower()

    if choice == "y":
        try:
            success = build_knowledge_base()

            if success:
                print("🎉 构建成功！")
                print()
                input("按回车键退出...")
            else:
                print()
                print("⚠️  构建失败，请检查上述错误信息")
                input("按回车键退出...")

        except KeyboardInterrupt:
            print("\n\n⚠️  构建已取消")
            input("按回车键退出...")
        except EOFError:
            pass  # 管道输入时忽略
        except Exception as e:
            print(f"\n❌ 发生错误：{e}")
            import traceback
            traceback.print_exc()
            try:
                input("按回车键退出...")
            except:
                pass
    else:
        print("构建已取消")
        print()
        print("提示：")
        print("  1. 确保 .env.dev 中配置了有效的 LLM_API_KEY")
        print("  2. 在 knowledge_base/ 目录下放入医疗文档")
        print("  3. 重新运行：python build_knowledge_base.py")
        print()
        try:
            input("按回车键退出...")
        except:
            pass


if __name__ == "__main__":
    main()
