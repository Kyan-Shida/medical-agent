"""
RAG 配置模块
"""

from pydantic import BaseModel, Field
from pathlib import Path
from typing import List
from config.base_config import BaseConfig


class RAGConfig(BaseModel):
    """RAG 配置类"""

    # 文本分割配置
    chunk_size: int = Field(default=500, description="文本块大小", ge=100, le=2000)
    chunk_overlap: int = Field(default=50, description="文本块重叠大小", ge=0, le=200)

    # 检索配置
    top_k: int = Field(default=3, description="检索返回数量", ge=1, le=10)
    score_threshold: float = Field(default=0.5, description="相似度阈值", ge=0.0, le=1.0)

    # 向量库配置
    faiss_index_path: str = Field(default="cache/faiss_index", description="FAISS 索引路径")
    embedding_model: str = Field(default="text-embedding-ada-002", description="嵌入模型")

    # 文档加载配置
    supported_extensions: List[str] = Field(
        default_factory=lambda: [".pdf", ".docx", ".txt", ".md"],
        description="支持的文档格式"
    )

    # 缓存配置
    enable_cache: bool = Field(default=True, description="是否启用检索缓存")
    cache_ttl: int = Field(default=1800, description="检索缓存 TTL(秒)")

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_env(cls, config: BaseConfig) -> "RAGConfig":
        """从环境变量加载配置"""
        return cls(
            chunk_size=config.get_int("CHUNK_SIZE", 500),
            chunk_overlap=config.get_int("CHUNK_OVERLAP", 50),
            top_k=config.get_int("TOP_K", 3),
            score_threshold=config.get_float("SCORE_THRESHOLD", 0.5),
            faiss_index_path=config.get("FAISS_INDEX_PATH", "cache/faiss_index"),
            embedding_model=config.get("EMBEDDING_MODEL", "text-embedding-ada-002"),
            enable_cache=config.get_bool("RAG_ENABLE_CACHE", True),
            cache_ttl=config.get_int("RAG_CACHE_TTL", 1800),
        )

    def get_faiss_index_path(self, project_root: Path) -> Path:
        """获取 FAISS 索引完整路径"""
        return project_root / self.faiss_index_path
