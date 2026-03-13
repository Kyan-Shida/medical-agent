﻿"""
文档加载模块
支持 PDF、DOCX、TXT 等格式
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from utils.log_utils import get_logger
from utils.exception_utils import DocumentLoadError

logger = get_logger(__name__)


@dataclass
class Document:
    """文档数据类"""

    content: str  # 文档内容
    metadata: Dict[str, Any]  # 元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """从字典创建"""
        return cls(
            content=data.get("content", ""),
            metadata=data.get("metadata", {}),
        )


class DocumentLoader:
    """文档加载器"""

    def __init__(self):
        """初始化文档加载器"""
        self.logger = get_logger(__name__)
        self.supported_formats = {
            ".txt": self._load_txt,
            ".md": self._load_txt,
            ".pdf": self._load_pdf,
            ".docx": self._load_docx,
        }

    def load_file(self, file_path: str) -> Document:
        """
        加载单个文件

        Args:
            file_path: 文件路径

        Returns:
            Document 对象

        Raises:
            DocumentLoadError: 加载失败
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise DocumentLoadError(
                message=f"文件不存在：{file_path}",
                code="FILE_NOT_FOUND",
                details={"path": str(file_path)},
            )

        # 获取文件扩展名
        suffix = file_path.suffix.lower()

        if suffix not in self.supported_formats:
            raise DocumentLoadError(
                message=f"不支持的文件格式：{suffix}",
                code="UNSUPPORTED_FORMAT",
                details={"extension": suffix, "supported": list(self.supported_formats.keys())},
            )

        try:
            # 加载文件
            content = self.supported_formats[suffix](file_path)

            # 创建文档对象
            doc = Document(
                content=content,
                metadata={
                    "source": str(file_path),
                    "filename": file_path.name,
                    "extension": suffix,
                    "size": file_path.stat().st_size,
                },
            )

            self.logger.info(f"文档加载成功：{file_path.name}, {len(content)} 字符")
            return doc

        except Exception as e:
            self.logger.error(f"文档加载失败：{file_path}, {e}")
            raise DocumentLoadError(
                message=f"文档加载失败：{str(e)}",
                code="LOAD_ERROR",
                details={"path": str(file_path)},
            )

    def load_directory(
        self,
        dir_path: str,
        extensions: Optional[List[str]] = None,
        recursive: bool = False,
    ) -> List[Document]:
        """
        加载目录下所有文档

        Args:
            dir_path: 目录路径
            extensions: 要加载的文件扩展名列表
            recursive: 是否递归加载子目录

        Returns:
            Document 对象列表
        """
        dir_path = Path(dir_path)

        if not dir_path.exists():
            raise DocumentLoadError(
                message=f"目录不存在：{dir_path}",
                code="DIR_NOT_FOUND",
            )

        if extensions is None:
            extensions = list(self.supported_formats.keys())

        documents = []

        # 遍历目录
        if recursive:
            file_iterator = dir_path.rglob("*")
        else:
            file_iterator = dir_path.glob("*")

        for file_path in file_iterator:
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                try:
                    doc = self.load_file(file_path)
                    documents.append(doc)
                except Exception as e:
                    self.logger.warning(f"跳过文件 {file_path}: {e}")

        self.logger.info(f"目录加载完成：{len(documents)} 个文档")
        return documents

    def _load_txt(self, file_path: Path) -> str:
        """加载 TXT 文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, "r", encoding="gbk") as f:
                return f.read()

    def _load_pdf(self, file_path: Path) -> str:
        """加载 PDF 文件"""
        try:
            from pypdf import PdfReader

            reader = PdfReader(file_path)
            text = ""

            for page in reader.pages:
                text += page.extract_text()

            return text

        except ImportError:
            self.logger.warning("pypdf 未安装，无法加载 PDF 文件")
            raise DocumentLoadError(
                message="需要安装 pypdf: pip install pypdf",
                code="MISSING_DEPENDENCY",
            )
        except Exception as e:
            raise DocumentLoadError(
                message=f"PDF 加载失败：{str(e)}",
                code="PDF_LOAD_ERROR",
            )

    def _load_docx(self, file_path: Path) -> str:
        """加载 DOCX 文件"""
        try:
            import docx2txt

            text = docx2txt.process(file_path)
            return text

        except ImportError:
            self.logger.warning("docx2txt 未安装，无法加载 DOCX 文件")
            raise DocumentLoadError(
                message="需要安装 docx2txt: pip install docx2txt",
                code="MISSING_DEPENDENCY",
            )
        except Exception as e:
            raise DocumentLoadError(
                message=f"DOCX 加载失败：{str(e)}",
                code="DOCX_LOAD_ERROR",
            )

    def load_from_text(self, text: str, source: str = "text") -> Document:
        """
        从文本字符串创建文档

        Args:
            text: 文本内容
            source: 来源标识

        Returns:
            Document 对象
        """
        return Document(
            content=text,
            metadata={
                "source": source,
                "type": "text",
            },
        )
