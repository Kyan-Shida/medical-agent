"""
文本分割模块
将长文本分割成适合向量化的块
"""

from typing import List, Dict, Any
from utils.log_utils import get_logger

logger = get_logger(__name__)


class TextSplitter:
    """文本分割器"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        length_function: callable = len,
    ):
        """
        初始化文本分割器

        Args:
            chunk_size: 每个文本块的大小（字符数）
            chunk_overlap: 文本块之间的重叠大小
            length_function: 长度计算函数
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.length_function = length_function
        self.logger = get_logger(__name__)

    def split_text(self, text: str) -> List[str]:
        """
        分割文本

        Args:
            text: 要分割的文本

        Returns:
            文本块列表
        """
        if not text:
            return []

        # 如果文本小于 chunk_size，直接返回
        if self.length_function(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            # 计算结束位置
            end = start + self.chunk_size

            # 如果已经到达文本末尾
            if end >= len(text):
                chunk = text[start:]
                chunks.append(chunk)
                break

            # 尝试在句子边界处分割
            chunk = text[start:end]

            # 查找最后的句子结束符
            sentence_enders = ["。", "！", "？", ".", "!", "?", "\n"]
            last_pos = -1

            for ender in sentence_enders:
                pos = chunk.rfind(ender)
                if pos > last_pos:
                    last_pos = pos

            # 如果找到句子结束符，调整 chunk
            if last_pos > self.chunk_size * 0.5:  # 至少在中间位置
                chunk = chunk[: last_pos + 1]

            chunks.append(chunk)

            # 移动起始位置（考虑重叠）
            start += self.chunk_size - self.chunk_overlap

        self.logger.info(f"文本分割完成：{len(chunks)} 个块")
        return chunks

    def split_documents(
        self, documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        分割文档列表

        Args:
            documents: 文档列表 [{"content": "...", "metadata": {...}}]

        Returns:
            分割后的文档列表
        """
        split_docs = []

        for doc in documents:
            content = doc.get("content", "")
            metadata = doc.get("metadata", {}).copy()

            # 分割文本
            chunks = self.split_text(content)

            # 为每个 chunk 创建文档
            for i, chunk in enumerate(chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update(
                    {
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "chunk_size": len(chunk),
                    }
                )

                split_docs.append(
                    {
                        "content": chunk,
                        "metadata": chunk_metadata,
                    }
                )

        self.logger.info(f"文档分割完成：{len(split_docs)} 个文本块")
        return split_docs

    def create_fixed_chunks(
        self, text: str, chunk_size: int = None
    ) -> List[str]:
        """
        创建固定大小的文本块

        Args:
            text: 要分割的文本
            chunk_size: 文本块大小（可选）

        Returns:
            文本块列表
        """
        if chunk_size is None:
            chunk_size = self.chunk_size

        chunks = []

        for i in range(0, len(text), chunk_size):
            chunk = text[i : i + chunk_size]
            chunks.append(chunk)

        return chunks

    def split_by_paragraph(self, text: str) -> List[str]:
        """
        按段落分割文本

        Args:
            text: 要分割的文本

        Returns:
            段落列表
        """
        # 按空行分割
        paragraphs = text.split("\n\n")

        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        self.logger.info(f"按段落分割：{len(paragraphs)} 个段落")
        return paragraphs

    def merge_small_chunks(
        self, chunks: List[str], min_size: int = 100
    ) -> List[str]:
        """
        合并过小的文本块

        Args:
            chunks: 文本块列表
            min_size: 最小文本块大小

        Returns:
            合并后的文本块列表
        """
        if not chunks:
            return []

        merged = []
        current_chunk = chunks[0]

        for chunk in chunks[1:]:
            if len(current_chunk) < min_size:
                # 合并到当前块
                current_chunk += "\n" + chunk
            else:
                # 保存当前块，开始新块
                merged.append(current_chunk)
                current_chunk = chunk

        # 添加最后一个块
        merged.append(current_chunk)

        self.logger.info(f"合并文本块：{len(chunks)} -> {len(merged)}")
        return merged
