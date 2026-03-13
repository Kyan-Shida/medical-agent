"""
多轮对话管理模块
"""

import json
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from utils.log_utils import get_logger
from utils.cache_utils import RedisCache

logger = get_logger(__name__)


@dataclass
class Message:
    """对话消息"""

    role: str
    content: str
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """从字典创建"""
        return cls(
            role=data.get("role", "user"),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", datetime.now().timestamp()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Conversation:
    """对话会话"""

    session_id: str
    messages: List[Message] = field(default_factory=list)
    created_at: float = field(default_factory=lambda: datetime.now().timestamp())
    updated_at: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: Dict[str, Any] = field(default_factory=dict)
    max_history_length: int = 20

    def add_message(self, role: str, content: str, **metadata) -> None:
        """
        添加消息

        Args:
            role: 角色（user/assistant/system）
            content: 消息内容
            **metadata: 元数据
        """
        message = Message(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        self.updated_at = datetime.now().timestamp()

        # 限制历史长度
        if len(self.messages) > self.max_history_length:
            self.messages = self.messages[-self.max_history_length :]

        logger.debug(f"添加消息：{role}, 当前消息数：{len(self.messages)}")

    def get_messages(self, include_system: bool = True) -> List[Dict[str, str]]:
        """
        获取消息列表（用于 LLM 调用）

        Args:
            include_system: 是否包含系统消息

        Returns:
            消息字典列表
        """
        messages = []

        for msg in self.messages:
            if not include_system and msg.role == "system":
                continue
            messages.append({"role": msg.role, "content": msg.content})

        return messages

    def get_last_message(self, role: Optional[str] = None) -> Optional[Message]:
        """
        获取最后一条消息

        Args:
            role: 指定角色（可选）

        Returns:
            最后一条消息
        """
        if not self.messages:
            return None

        if role is None:
            return self.messages[-1]

        # 从后往前查找指定角色的消息
        for msg in reversed(self.messages):
            if msg.role == role:
                return msg

        return None

    def clear_history(self) -> None:
        """清空历史消息"""
        self.messages = []
        self.updated_at = datetime.now().timestamp()
        logger.info(f"清空对话历史：{self.session_id}")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
            "max_history_length": self.max_history_length,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Conversation":
        """从字典创建"""
        conv = cls(
            session_id=data.get("session_id", ""),
            created_at=data.get("created_at", datetime.now().timestamp()),
            updated_at=data.get("updated_at", datetime.now().timestamp()),
            metadata=data.get("metadata", {}),
            max_history_length=data.get("max_history_length", 20),
        )

        for msg_data in data.get("messages", []):
            conv.messages.append(Message.from_dict(msg_data))

        return conv


class ConversationManager:
    """对话管理器"""

    def __init__(self, cache: Optional[RedisCache] = None, ttl: int = 3600):
        """
        初始化对话管理器

        Args:
            cache: Redis 缓存实例
            ttl: 会话 TTL（秒）
        """
        self.cache = cache
        self.ttl = ttl
        self.in_memory_sessions: Dict[str, Conversation] = {}
        self.logger = get_logger(__name__)

    def create_session(
        self,
        session_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **metadata,
    ) -> Conversation:
        """
        创建新会话

        Args:
            session_id: 会话 ID（可选，自动生成）
            system_prompt: 系统提示
            **metadata: 元数据

        Returns:
            会话对象
        """
        if session_id is None:
            session_id = self._generate_session_id()

        conversation = Conversation(
            session_id=session_id,
            metadata=metadata,
        )

        # 添加系统提示
        if system_prompt:
            conversation.add_message(role="system", content=system_prompt)

        self.logger.info(f"创建会话：{session_id}")
        return conversation

    def get_session(self, session_id: str) -> Optional[Conversation]:
        """
        获取会话

        Args:
            session_id: 会话 ID

        Returns:
            会话对象，不存在返回 None
        """
        # 优先从内存获取
        if session_id in self.in_memory_sessions:
            self.logger.debug(f"从内存获取会话：{session_id}")
            return self.in_memory_sessions[session_id]

        # 从缓存获取
        if self.cache:
            try:
                cached = self.cache.get(f"conversation:{session_id}")
                if cached:
                    conversation = Conversation.from_dict(cached)
                    # 写回内存
                    self.in_memory_sessions[session_id] = conversation
                    self.logger.debug(f"从缓存获取会话：{session_id}")
                    return conversation
            except Exception as e:
                self.logger.error(f"从缓存获取会话失败：{e}")

        self.logger.warning(f"会话不存在：{session_id}")
        return None

    def save_session(self, conversation: Conversation) -> bool:
        """
        保存会话

        Args:
            conversation: 会话对象

        Returns:
            保存是否成功
        """
        session_id = conversation.session_id

        # 保存到内存
        self.in_memory_sessions[session_id] = conversation

        # 保存到缓存
        if self.cache:
            try:
                self.cache.set(
                    f"conversation:{session_id}",
                    conversation.to_dict(),
                    self.ttl,
                )
                self.logger.debug(f"保存会话到缓存：{session_id}")
                return True
            except Exception as e:
                self.logger.error(f"保存会话到缓存失败：{e}")
                return False

        return True

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话

        Args:
            session_id: 会话 ID

        Returns:
            删除是否成功
        """
        # 从内存删除
        if session_id in self.in_memory_sessions:
            del self.in_memory_sessions[session_id]

        # 从缓存删除
        if self.cache:
            try:
                self.cache.delete(f"conversation:{session_id}")
                self.logger.info(f"删除会话：{session_id}")
                return True
            except Exception as e:
                self.logger.error(f"删除会话失败：{e}")
                return False

        return True

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        **metadata,
    ) -> bool:
        """
        添加消息到会话

        Args:
            session_id: 会话 ID
            role: 角色
            content: 内容
            **metadata: 元数据

        Returns:
            添加是否成功
        """
        conversation = self.get_session(session_id)

        if not conversation:
            self.logger.error(f"会话不存在：{session_id}")
            return False

        conversation.add_message(role=role, content=content, **metadata)
        return self.save_session(conversation)

    def get_conversation_history(
        self, session_id: str, limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        获取对话历史

        Args:
            session_id: 会话 ID
            limit: 返回数量

        Returns:
            消息列表
        """
        conversation = self.get_session(session_id)

        if not conversation:
            return []

        messages = conversation.get_messages()

        # 返回最近 N 条
        if limit > 0:
            messages = messages[-limit:]

        return messages

    def _generate_session_id(self) -> str:
        """生成会话 ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:16]

    def cleanup_expired(self) -> int:
        """
        清理过期会话

        Returns:
            清理的会话数量
        """
        count = 0

        # 清理内存中的过期会话
        current_time = datetime.now().timestamp()
        expired_sessions = []

        for session_id, conversation in self.in_memory_sessions.items():
            if current_time - conversation.updated_at > self.ttl:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self.delete_session(session_id)
            count += 1

        self.logger.info(f"清理 {count} 个过期会话")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "active_sessions": len(self.in_memory_sessions),
            "ttl": self.ttl,
            "cache_connected": self.cache.is_connected() if self.cache else False,
        }
