"""
RAG 模块单元测试
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.rag_config import RAGConfig
from core.rag.document_loader import DocumentLoader, Document
from core.rag.text_splitter import TextSplitter
from core.rag.vector_store import VectorStore, EmbeddingClient
from core.rag.retriever import Retriever
from utils.exception_utils import DocumentLoadError


class TestDocumentLoader:
    """测试文档加载器"""

    def test_load_txt(self, tmp_path):
        """测试加载 TXT 文件"""
        # 创建测试文件
        test_file = tmp_path / "test.txt"
        test_content = "这是一个测试文档\n第二行内容"
        test_file.write_text(test_content, encoding="utf-8")

        # 加载
        loader = DocumentLoader()
        doc = loader.load_file(str(test_file))

        assert isinstance(doc, Document)
        assert doc.content == test_content
        assert doc.metadata["filename"] == "test.txt"
        assert doc.metadata["extension"] == ".txt"

    def test_load_from_text(self):
        """测试从文本创建文档"""
        loader = DocumentLoader()
        doc = loader.load_from_text("测试内容", source="test")

        assert doc.content == "测试内容"
        assert doc.metadata["source"] == "test"

    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        loader = DocumentLoader()

        with pytest.raises(DocumentLoadError):
            loader.load_file("nonexistent.txt")

    def test_load_unsupported_format(self, tmp_path):
        """测试加载不支持的格式"""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("content")

        loader = DocumentLoader()

        with pytest.raises(DocumentLoadError):
            loader.load_file(str(test_file))

    def test_load_directory(self, tmp_path):
        """测试加载目录"""
        # 创建测试文件
        for i in range(3):
            test_file = tmp_path / f"test{i}.txt"
            test_file.write_text(f"内容{i}", encoding="utf-8")

        loader = DocumentLoader()
        docs = loader.load_directory(str(tmp_path))

        assert len(docs) == 3


class TestTextSplitter:
    """测试文本分割器"""

    def test_split_short_text(self):
        """测试分割短文本"""
        splitter = TextSplitter(chunk_size=100, chunk_overlap=10)
        text = "这是一段短文本"

        chunks = splitter.split_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_split_long_text(self):
        """测试分割长文本"""
        splitter = TextSplitter(chunk_size=50, chunk_overlap=10)
        text = "这是一段很长的文本。" * 20  # 重复 20 次

        chunks = splitter.split_text(text)

        assert len(chunks) > 1
        assert all(len(chunk) <= 60 for chunk in chunks)  # 允许少量超出

    def test_split_by_sentence(self):
        """测试按句子分割"""
        splitter = TextSplitter(chunk_size=100, chunk_overlap=0)
        text = "这是第一句。这是第二句。这是第三句。"

        chunks = splitter.split_text(text)

        # 应该在句子边界处分割
        assert len(chunks) > 0
        assert all("。" in chunk or len(chunk) < 100 for chunk in chunks)

    def test_split_documents(self):
        """测试分割文档列表"""
        splitter = TextSplitter(chunk_size=50, chunk_overlap=10)

        documents = [
            {"content": "文档 1 内容。" * 10, "metadata": {"source": "doc1"}},
            {"content": "文档 2 内容。" * 10, "metadata": {"source": "doc2"}},
        ]

        split_docs = splitter.split_documents(documents)

        assert len(split_docs) > 2
        assert all("content" in doc for doc in split_docs)
        assert all("metadata" in doc for doc in split_docs)

    def test_split_by_paragraph(self):
        """测试按段落分割"""
        splitter = TextSplitter()
        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"

        paragraphs = splitter.split_by_paragraph(text)

        assert len(paragraphs) == 3
        assert paragraphs[0] == "第一段内容。"
        assert paragraphs[1] == "第二段内容。"

    def test_merge_small_chunks(self):
        """测试合并小文本块"""
        splitter = TextSplitter()
        chunks = ["小", "小 chunk", "足够大的文本块", "小"]

        merged = splitter.merge_small_chunks(chunks, min_size=10)

        assert len(merged) < len(chunks)


class TestEmbeddingClient:
    """测试 Embedding 客户端"""

    @pytest.mark.skip(reason="需要真实的 API Key")
    def test_get_embedding(self):
        """测试获取向量"""
        config = BaseConfig(env_file=".env.dev")
        api_key = config.get("LLM_API_KEY")

        client = EmbeddingClient(api_key=api_key)
        embedding = client.get_embedding("测试文本")

        assert embedding is not None
        assert len(embedding) > 0
        assert embedding.dtype == np.float32

    @pytest.mark.skip(reason="需要真实的 API Key")
    def test_get_embeddings_batch(self):
        """测试批量获取向量"""
        config = BaseConfig(env_file=".env.dev")
        api_key = config.get("LLM_API_KEY")

        client = EmbeddingClient(api_key=api_key)
        texts = ["文本 1", "文本 2", "文本 3"]

        embeddings = client.get_embeddings_batch(texts)

        assert len(embeddings) == len(texts)
        assert all(len(e) > 0 for e in embeddings)


class TestVectorStore:
    """测试向量存储"""

    @pytest.mark.skip(reason="需要真实的 API Key")
    def test_add_and_search(self, tmp_path):
        """测试添加和搜索"""
        config = BaseConfig(env_file=".env.dev")
        api_key = config.get("LLM_API_KEY")

        # 创建组件
        embedding_client = EmbeddingClient(api_key=api_key)
        vector_store = VectorStore(
            index_path=str(tmp_path / "faiss_index"),
            embedding_client=embedding_client,
        )

        # 添加文档
        documents = [
            {"content": "儿童发烧怎么办？", "metadata": {"category": "儿科"}},
            {"content": "感冒吃什么药？", "metadata": {"category": "内科"}},
            {"content": "如何预防高血压？", "metadata": {"category": "心血管"}},
        ]

        doc_ids = vector_store.add_documents(documents)
        assert len(doc_ids) == 3

        # 搜索
        results = vector_store.similarity_search("发烧", top_k=2)

        assert len(results) > 0
        assert "发烧" in results[0][0].content or "儿童" in results[0][0].content

    @pytest.mark.skip(reason="需要真实的 API Key")
    def test_persistence(self, tmp_path):
        """测试持久化"""
        config = BaseConfig(env_file=".env.dev")
        api_key = config.get("LLM_API_KEY")

        embedding_client = EmbeddingClient(api_key=api_key)
        index_path = tmp_path / "faiss_index"

        # 创建并添加文档
        vector_store1 = VectorStore(
            index_path=str(index_path),
            embedding_client=embedding_client,
        )

        documents = [{"content": "测试内容", "metadata": {}}]
        vector_store1.add_documents(documents)

        # 重新加载
        vector_store2 = VectorStore(
            index_path=str(index_path),
            embedding_client=embedding_client,
        )

        # 验证文档存在
        stats = vector_store2.get_stats()
        assert stats["document_count"] > 0


class TestRetriever:
    """测试检索器"""

    @pytest.mark.skip(reason="需要真实的 API Key")
    def test_retrieve(self, tmp_path):
        """测试检索"""
        config = BaseConfig(env_file=".env.dev")
        api_key = config.get("LLM_API_KEY")

        # 创建组件
        embedding_client = EmbeddingClient(api_key=api_key)
        vector_store = VectorStore(
            index_path=str(tmp_path / "faiss_index"),
            embedding_client=embedding_client,
        )

        # 添加测试文档
        documents = [
            {"content": "儿童发烧应该吃什么药？", "metadata": {"category": "儿科"}},
            {"content": "成人感冒可以自行服药", "metadata": {"category": "内科"}},
        ]
        vector_store.add_documents(documents)

        # 创建检索器
        retriever = Retriever(
            vector_store=vector_store,
            embedding_client=embedding_client,
            top_k=2,
        )

        # 检索
        results = retriever.retrieve("儿童发烧")

        assert len(results) > 0
        assert any("儿童" in doc.content or "发烧" in doc.content for doc, _ in results)

    @pytest.mark.skip(reason="需要真实的 API Key")
    def test_retrieve_with_context(self, tmp_path):
        """测试检索并生成上下文"""
        config = BaseConfig(env_file=".env.dev")
        api_key = config.get("LLM_API_KEY")

        embedding_client = EmbeddingClient(api_key=api_key)
        vector_store = VectorStore(
            index_path=str(tmp_path / "faiss_index"),
            embedding_client=embedding_client,
        )

        documents = [
            {"content": "儿童发烧处理建议：多喝水，适当休息", "metadata": {}},
        ]
        vector_store.add_documents(documents)

        retriever = Retriever(
            vector_store=vector_store,
            embedding_client=embedding_client,
        )

        context = retriever.retrieve_with_context("儿童发烧怎么办")

        assert len(context) > 0
        assert "发烧" in context


class TestRAGConfig:
    """测试 RAG 配置"""

    def test_config_from_env(self):
        """测试从环境变量加载配置"""
        config = BaseConfig(env_file=".env.test")
        rag_config = RAGConfig.from_env(config)

        assert rag_config.chunk_size == 500
        assert rag_config.top_k == 3

    def test_config_validation(self):
        """测试配置验证"""
        rag_config = RAGConfig(
            chunk_size=500,
            chunk_overlap=50,
            top_k=3,
        )

        assert rag_config.chunk_size > 0
        assert rag_config.top_k > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
