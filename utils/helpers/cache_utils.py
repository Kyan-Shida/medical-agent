"""
缓存工具模块（Redis�?"""

import json
import hashlib
from typing import Any, Optional, Dict, Union
from datetime import timedelta
import redis
from utils.logging.log_utils import get_logger
from utils.exceptions.exception_utils import CacheError

logger = get_logger(__name__)


class RedisCache:
    """Redis 缓存封装"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        socket_timeout: int = 5,
        prefix: str = "medical_agent:",
    ):
        """
        初始�?Redis 缓存

        Args:
            host: Redis 主机
            port: Redis 端口
            db: Redis 数据�?            password: Redis 密码
            socket_timeout: 连接超时
            prefix: Key 前缀
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.socket_timeout = socket_timeout
        self.prefix = prefix
        self._client: Optional[redis.Redis] = None
        self.logger = get_logger(__name__)

    def connect(self) -> bool:
        """
        连接 Redis

        Returns:
            连接是否成功
        """
        try:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                socket_timeout=self.socket_timeout,
                decode_responses=True,
            )
            # 测试连接
            self._client.ping()
            self.logger.info(f"Redis 连接成功：{self.host}:{self.port}")
            return True

        except redis.RedisError as e:
            self.logger.error(f"Redis 连接失败：{e}")
            self._client = None
            return False

    def is_connected(self) -> bool:
        """检查是否已连接"""
        if self._client is None:
            return False

        try:
            self._client.ping()
            return True
        except redis.RedisError:
            return False

    def _get_key(self, key: str) -> str:
        """获取带前缀�?key"""
        return f"{self.prefix}{key}"

    def _serialize(self, value: Any) -> str:
        """序列化�?""
        try:
            return json.dumps(value, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            self.logger.error(f"序列化失败：{e}")
            raise CacheError(message=f"序列化失败：{e}", code="SERIALIZE_ERROR")

    def _deserialize(self, value: str) -> Any:
        """反序列化�?""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError) as e:
            self.logger.error(f"反序列化失败：{e}")
            return None

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        根据参数生成缓存 key

        Args:
            prefix: 前缀
            *args: 位置参数
            **kwargs: 关键字参�?
        Returns:
            缓存 key
        """
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{self.prefix}{prefix}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存

        Args:
            key: 缓存�?
        Returns:
            缓存值，不存在返�?None
        """
        if not self._client:
            return None

        try:
            full_key = self._get_key(key)
            value = self._client.get(full_key)

            if value is None:
                return None

            return self._deserialize(value)

        except redis.RedisError as e:
            self.logger.error(f"Redis 读取失败：{e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        设置缓存

        Args:
            key: 缓存�?            value: 缓存�?            ttl: 过期时间（秒�?
        Returns:
            设置是否成功
        """
        if not self._client:
            return False

        try:
            full_key = self._get_key(key)
            serialized = self._serialize(value)

            if ttl:
                result = self._client.setex(full_key, ttl, serialized)
            else:
                result = self._client.set(full_key, serialized)

            return bool(result)

        except redis.RedisError as e:
            self.logger.error(f"Redis 写入失败：{e}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存

        Args:
            key: 缓存�?
        Returns:
            删除是否成功
        """
        if not self._client:
            return False

        try:
            full_key = self._get_key(key)
            result = self._client.delete(full_key)
            return result > 0

        except redis.RedisError as e:
            self.logger.error(f"Redis 删除失败：{e}")
            return False

    def exists(self, key: str) -> bool:
        """
        检查缓存是否存�?
        Args:
            key: 缓存�?
        Returns:
            是否存在
        """
        if not self._client:
            return False

        try:
            full_key = self._get_key(key)
            return bool(self._client.exists(full_key))

        except redis.RedisError as e:
            self.logger.error(f"Redis 检查失败：{e}")
            return False

    def cache(
        self,
        prefix: str = "cache",
        ttl: int = 3600,
        key_func: Optional[callable] = None,
    ):
        """
        缓存装饰�?
        Args:
            prefix: 缓存 key 前缀
            ttl: 缓存 TTL
            key_func: 自定�?key 生成函数

        Returns:
            装饰�?        """

        def decorator(func):
            import functools

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存 key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_key(prefix, *args, **kwargs)

                # 尝试从缓存获�?                cached_value = self.get(cache_key)
                if cached_value is not None:
                    self.logger.debug(f"缓存命中：{cache_key}")
                    return cached_value

                # 执行函数
                result = func(*args, **kwargs)

                # 写入缓存
                if result is not None:
                    self.set(cache_key, result, ttl)
                    self.logger.debug(f"缓存已设置：{cache_key}")

                return result

            return wrapper

        return decorator

    def clear_prefix(self, prefix: str) -> int:
        """
        清除指定前缀的所有缓�?
        Args:
            prefix: 前缀

        Returns:
            删除�?key 数量
        """
        if not self._client:
            return 0

        try:
            pattern = f"{self.prefix}{prefix}*"
            count = 0
            cursor = 0

            while True:
                cursor, keys = self._client.scan(cursor, match=pattern, count=100)
                if keys:
                    count += self._client.delete(*keys)
                if cursor == 0:
                    break

            self.logger.info(f"清除缓存：{prefix}, 删除 {count} �?key")
            return count

        except redis.RedisError as e:
            self.logger.error(f"Redis 清除失败：{e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        获取 Redis 统计信息

        Returns:
            统计信息字典
        """
        if not self._client:
            return {"connected": False}

        try:
            info = self._client.info("stats")
            return {
                "connected": True,
                "total_connections_received": info.get("total_connections_received", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }

        except redis.RedisError as e:
            self.logger.error(f"Redis 统计获取失败：{e}")
            return {"connected": False, "error": str(e)}
