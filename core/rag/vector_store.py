"""
向量存储模块
使用 FAISS 进行向量存储和检索
使用智谱 AI Embedding API 进行向量化
"""

import json
import pickle
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from utils.log_utils import get_logger
from utils.exception_utils import VectorStoreError
from config.base_config import BaseConfig

logger = get_logger(__name__)


@dataclass
class VectorDocument:
    """向量文档"""

    id: str  # 文档 ID
    content: str  # 文本内容
    embedding: np.ndarray  # 向量
    metadata: Dict[str, Any]  # 元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding.tolist(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VectorDocument":
        """从字典创建"""
        return cls(
            id=data.get("id", ""),
            content=data.get("content", ""),
            embedding=np.array(data.get("embedding", [])),
            metadata=data.get("metadata", {}),
        )


class EmbeddingClient:
    """智谱 AI Embedding 客户端"""

    def __init__(self, api_key: str, model: str = "embedding-2"):
        """
        初始化 Embedding 客户端

        Args:
            api_key: API Key
            model: Embedding 模型
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://open.bigmodel.cn/api/paas/v4"
        self.logger = get_logger(__name__)

    def get_embedding(self, text: str) -> np.ndarray:
        """
        获取文本的向量表示

        Args:
            text: 输入文本

        Returns:
            向量数组

        Raises:
            VectorStoreError: 获取失败
        """
        try:
            # 构建请求
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": self.model,
                "input": text,
            }

            # 发送请求
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
                timeout=30,
            )

            if response.status_code != 200:
                raise VectorStoreError(
                    message=f"Embedding API 请求失败：{response.status_code}",
                    code="EMBEDDING_API_ERROR",
                    details={"response": response.text[:500]},
                )

            # 解析响应
            result = response.json()
            embedding = result["data"][0]["embedding"]

            return np.array(embedding, dtype=np.float32)

        except requests.exceptions.Timeout:
            raise VectorStoreError(
                message="Embedding 请求超时",
                code="EMBEDDING_TIMEOUT",
            )
        except Exception as e:
            self.logger.error(f"获取 Embedding 失败：{e}")
            raise VectorStoreError(
                message=f"获取 Embedding 失败：{str(e)}",
                code="EMBEDDING_ERROR",
            )

    def get_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[np.ndarray]:
        """
        批量获取向量

        Args:
            texts: 文本列表
            batch_size: 批次大小

        Returns:
            向量列表
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]
            
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }

                payload = {
                    "model": self.model,
                    "input": batch_texts,
                }

                response = requests.post(
                    f"{self.base_url}/embeddings",
                    headers=headers,
                    json=payload,
                    timeout=60,
                )

                if response.status_code != 200:
                    raise VectorStoreError(
                        message=f"Embedding API 请求失败：{response.status_code}",
                        code="EMBEDDING_API_ERROR",
                    )

                result = response.json()
                batch_embeddings = [item["embedding"] for item in result["data"]]
                embeddings.extend([np.array(e, dtype=np.float32) for e in batch_embeddings])

            except Exception as e:
                self.logger.error(f"批量获取 Embedding 失败：{e}")
                raise VectorStoreError(
                    message=f"批量获取 Embedding 失败：{str(e)}",
                    code="BATCH_EMBEDDING_ERROR",
                )

        return embeddings


class VectorStore:
    """向量存储（FAISS 封装）"""

    def __init__(
        self,
        index_path: str,
        embedding_client: EmbeddingClient,
        dimension: int = 1024,  # embedding-2 的维度
    ):
        """
        初始化向量存储

        Args:
            index_path: FAISS 索引路径
            embedding_client: Embedding 客户端
            dimension: 向量维度
        """
        self.index_path = Path(index_path)
        self.embedding_client = embedding_client
        self.dimension = dimension
        self.logger = get_logger(__name__)

        # FAISS 索引
        self.index = None
        self.documents: Dict[str, VectorDocument] = {}

        # 尝试加载已有索引
        self._load_index()

    def _load_index(self) -> bool:
        """加载已有索引"""
        try:
            if self.index_path.exists():
                # 加载 FAISS 索引
                import faiss

                faiss_path = self.index_path / "faiss.index"
                if faiss_path.exists():
                    self.index = faiss.read_index(str(faiss_path))

                # 加载文档元数据
                doc_path = self.index_path / "documents.pkl"
                if doc_path.exists():
                    with open(doc_path, "rb") as f:
                        self.documents = pickle.load(f)

                self.logger.info(f"加载向量索引：{len(self.documents)} 个文档")
                return True

        except Exception as e:
            self.logger.error(f"加载向量索引失败：{e}")

        return False

    def _save_index(self) -> bool:
        """保存索引"""
        try:
            # 创建目录
            self.index_path.mkdir(parents=True, exist_ok=True)

            # 保存 FAISS 索引
            if self.index is not None:
                import faiss

                faiss_path = self.index_path / "faiss.index"
                faiss.write_index(self.index, str(faiss_path))

            # 保存文档元数据
            doc_path = self.index_path / "documents.pkl"
            with open(doc_path, "wb") as f:
                pickle.dump(self.documents, f)

            self.logger.info(f"保存向量索引：{len(self.documents)} 个文档")
            return True

        except Exception as e:
            self.logger.error(f"保存向量索引失败：{e}")
            return False

    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        添加文档到向量库

        Args:
            documents: 文档列表 [{"content": "...", "metadata": {...}}]

        Returns:
            文档 ID 列表
        """
        import faiss

        if not documents:
            return []

        self.logger.info(f"添加 {len(documents)} 个文档到向量库")

        # 提取内容
        texts = [doc["content"] for doc in documents]

        # 获取向量
        embeddings = self.embedding_client.get_embeddings_batch(texts)

        # 创建 FAISS 索引（如果不存在）
        if self.index is None:
            self.index = faiss.IndexFlatIP(len(embeddings[0]))  # 使用内积相似度

        # 添加向量到索引
        embedding_array = np.array(embeddings, dtype=np.float32)
        self.index.add(embedding_array)

        # 创建文档对象
        doc_ids = []
        for i, doc in enumerate(documents):
            # 生成文档 ID
            doc_id = hashlib.md5(
                f"{doc['content'][:100]}:{i}".encode()
            ).hexdigest()[:16]

            vector_doc = VectorDocument(
                id=doc_id,
                content=doc["content"],
                embedding=embeddings[i],
                metadata=doc.get("metadata", {}),
            )

            self.documents[doc_id] = vector_doc
            doc_ids.append(doc_id)

        # 保存索引
        self._save_index()

        self.logger.info(f"成功添加 {len(doc_ids)} 个文档")
        return doc_ids

    def similarity_search(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.5,
    ) -> List[Tuple[VectorDocument, float]]:
        """
        相似度搜索

        Args:
            query: 查询文本
            top_k: 返回数量
            score_threshold: 相似度阈值

        Returns:
            (文档，相似度分数) 列表
        """
        if self.index is None or len(self.documents) == 0:
            self.logger.warning("向量库为空")
            return []

        # 获取查询向量
        query_embedding = self.embedding_client.get_embedding(query)
        query_embedding = np.array([query_embedding], dtype=np.float32)

        # 搜索
        scores, indices = self.index.search(query_embedding, top_k)

        # 获取文档
        results = []
        doc_ids = list(self.documents.keys())

        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < 0 or idx >= len(doc_ids):
                continue

            doc_id = doc_ids[idx]
            doc = self.documents[doc_id]

            # 归一化分数到 0-1
            normalized_score = (score + 1) / 2

            if normalized_score >= score_threshold:
                results.append((doc, float(normalized_score)))

        self.logger.info(f"相似度搜索：找到 {len(results)} 个结果")
        return results

    def search_with_metadata(
        self,
        query: str,
        top_k: int = 3,
        filter_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[VectorDocument, float]]:
        """
        带元数据过滤的搜索

        Args:
            query: 查询文本
            top_k: 返回数量
            filter_metadata: 元数据过滤条件

        Returns:
            (文档，相似度分数) 列表
        """
        # 先进行相似度搜索
        results = self.similarity_search(query, top_k * 2)  # 多取一些用于过滤

        # 元数据过滤
        if filter_metadata:
            filtered_results = []

            for doc, score in results:
                match = True

                for key, value in filter_metadata.items():
                    if doc.metadata.get(key) != value:
                        match = False
                        break

                if match:
                    filtered_results.append((doc, score))

            results = filtered_results[:top_k]

        return results

    def delete_documents(self, doc_ids: List[str]) -> bool:
        """
        删除文档

        Args:
            doc_ids: 文档 ID 列表

        Returns:
            删除是否成功
        """
        # FAISS 不支持直接删除，需要重建索引
        for doc_id in doc_ids:
            if doc_id in self.documents:
                del self.documents[doc_id]

        # 重建索引
        self._rebuild_index()

        self.logger.info(f"删除 {len(doc_ids)} 个文档")
        return True

    def _rebuild_index(self):
        """重建索引"""
        import faiss

        # 清空索引
        self.index = None

        if not self.documents:
            return

        # 重新添加所有文档
        documents = [
            {"content": doc.content, "metadata": doc.metadata}
            for doc in self.documents.values()
        ]

        self.add_documents(documents)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "document_count": len(self.documents),
            "index_path": str(self.index_path),
            "dimension": self.dimension,
            "index_type": type(self.index).__name__ if self.index else "None",
        }

    def clear(self) -> bool:
        """清空向量库"""
        self.index = None
        self.documents = {}

        # 删除索引文件
        if self.index_path.exists():
            import shutil

            shutil.rmtree(self.index_path)

        self.logger.info("向量库已清空")
        return True
