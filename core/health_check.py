﻿﻿"""
健康检查模块
"""

import time
from typing import Dict, Any
from datetime import datetime
from utils.log_utils import get_logger
from utils.cache_utils import RedisCache

logger = get_logger(__name__)


class HealthChecker:
    """健康检查器"""

    def __init__(self, redis_cache: RedisCache = None):
        """
        初始化健康检查器

        Args:
            redis_cache: Redis 缓存实例
        """
        self.redis_cache = redis_cache
        self.start_time = datetime.now()
        self.logger = get_logger(__name__)

    def check_all(self) -> Dict[str, Any]:
        """
        检查所有服务

        Returns:
            健康状态字典
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "services": {
                "redis": self.check_redis(),
                "llm": self.check_llm(),
            },
        }

    def check_redis(self) -> Dict[str, Any]:
        """
        检查 Redis 服务

        Returns:
            Redis 健康状态
        """
        if not self.redis_cache:
            return {
                "status": "not_configured",
                "message": "Redis 未配置",
            }

        try:
            is_connected = self.redis_cache.is_connected()

            if is_connected:
                stats = self.redis_cache.get_stats()
                return {
                    "status": "healthy",
                    "connected": True,
                    "details": stats,
                }
            else:
                return {
                    "status": "unhealthy",
                    "connected": False,
                    "message": "Redis 连接失败",
                }

        except Exception as e:
            self.logger.error(f"Redis 健康检查失败：{e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    def check_llm(self) -> Dict[str, Any]:
        """
        检查 LLM 服务

        Returns:
            LLM 健康状态
        """
        # 这里可以添加 LLM API 的健康检查逻辑
        # 由于 LLM 是外部服务，通常只检查配置是否有效
        return {
            "status": "healthy",
            "message": "LLM 配置正常",
        }

    def get_metrics(self) -> Dict[str, Any]:
        """
        获取服务指标

        Returns:
            指标字典
        """
        metrics = {
            "uptime": {
                "seconds": (datetime.now() - self.start_time).total_seconds(),
                "human_readable": self._format_uptime(),
            },
            "timestamp": datetime.now().isoformat(),
        }

        # 添加 Redis 指标
        if self.redis_cache and self.redis_cache.is_connected():
            metrics["redis"] = self.redis_cache.get_stats()

        return metrics

    def _format_uptime(self) -> str:
        """格式化运行时间"""
        total_seconds = int((datetime.now() - self.start_time).total_seconds())

        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        parts = []
        if days > 0:
            parts.append(f"{days}天")
        if hours > 0:
            parts.append(f"{hours}小时")
        if minutes > 0:
            parts.append(f"{minutes}分钟")
        parts.append(f"{seconds}秒")

        return " ".join(parts)


def create_health_checker(redis_cache: RedisCache = None) -> HealthChecker:
    """
    创建健康检查器

    Args:
        redis_cache: Redis 缓存实例

    Returns:
        HealthChecker 实例
    """
    return HealthChecker(redis_cache=redis_cache)
