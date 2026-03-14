"""
检索模块
封装向量检索逻辑，支持缓存和并行检索
"""

from typing import List, Dict, Any, Optional, Tuple
from utils.log_utils import get_logger
from utils.cache_utils import RedisCache
from core.rag.vector_store import VectorStore, VectorDocument, EmbeddingClient

logger = get_logger(__name__)


class Retriever:
    """检索器"""

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_client: EmbeddingClient,
        cache: Optional[RedisCache] = None,
        top_k: int = 3,
        score_threshold: float = 0.5,
    ):
        """
        初始化检索器

        Args:
            vector_store: 向量存储
            embedding_client: Embedding 客户端
            cache: Redis 缓存
            top_k: 默认返回数量
            score_threshold: 默认相似度阈值
        """
        self.vector_store = vector_store
        self.embedding_client = embedding_client
        self.cache = cache
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.logger = get_logger(__name__)

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        score_threshold: Optional[float] = None,
        use_cache: bool = True,
    ) -> List[Tuple[VectorDocument, float]]:
        """
        检索相关文档

        Args:
            query: 查询文本
            top_k: 返回数量
            score_threshold: 相似度阈值
            use_cache: 是否使用缓存

        Returns:
            (文档，相似度分数) 列表
        """
        if top_k is None:
            top_k = self.top_k

        if score_threshold is None:
            score_threshold = self.score_threshold

        # 尝试从缓存获取
        cache_key = None
        if use_cache and self.cache:
            cache_key = f"retrieve:{query[:50]}:{top_k}:{score_threshold}"
            cached_result = self.cache.get(cache_key)

            if cached_result:
                self.logger.debug(f"检索缓存命中：{query[:30]}")
                return cached_result

        # 执行检索
        self.logger.info(f"检索：{query[:50]}...")
        results = self.vector_store.similarity_search(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold,
        )

        # 保存到缓存
        if cache_key and self.cache:
            self.cache.set(cache_key, results, ttl=1800)  # 30 分钟缓存

        self.logger.info(f"检索完成：{len(results)} 个结果")
        return results

    def retrieve_with_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        include_metadata: bool = True,
    ) -> str:
        """
        检索并生成上下文文本

        Args:
            query: 查询文本
            top_k: 返回数量
            include_metadata: 是否包含元数据

        Returns:
            上下文文本
        """
        results = self.retrieve(query, top_k=top_k)

        if not results:
            return ""

        # 拼接上下文
        context_parts = []

        for doc, score in results:
            context_part = doc.content

            # 添加元数据
            if include_metadata and doc.metadata:
                source = doc.metadata.get("source", "")
                filename = doc.metadata.get("filename", "")

                if filename:
                    context_part = f"[来源：{filename}]\n{context_part}"

            context_parts.append(context_part)

        context = "\n\n".join(context_parts)
        self.logger.debug(f"生成上下文：{len(context)} 字符")

        return context

    def batch_retrieve(
        self,
        queries: List[str],
        top_k: Optional[int] = None,
    ) -> Dict[str, List[Tuple[VectorDocument, float]]]:
        """
        批量检索

        Args:
            queries: 查询列表
            top_k: 返回数量

        Returns:
            查询 -> 结果 的映射
        """
        results = {}

        for query in queries:
            query_results = self.retrieve(query, top_k=top_k)
            results[query] = query_results

        return results

    def get_relevant_chunks(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        获取相关文本块

        Args:
            query: 查询文本
            top_k: 返回数量

        Returns:
            文本块列表
        """
        results = self.retrieve(query, top_k=top_k)

        chunks = []
        for doc, score in results:
            chunks.append(
                {
                    "content": doc.content,
                    "score": score,
                    "metadata": doc.metadata,
                }
            )

        return chunks

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "vector_store": self.vector_store.get_stats(),
            "cache_connected": self.cache.is_connected() if self.cache else False,
            "top_k": self.top_k,
            "score_threshold": self.score_threshold,
        }
