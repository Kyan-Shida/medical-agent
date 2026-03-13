"""
安全工具模块（脱敏、鉴权、限流）
"""

import re
import hashlib
import time
from typing import Optional, Dict, Any
from functools import wraps
import redis
from utils.exception_utils import AuthenticationError, RateLimitError
from utils.log_utils import get_logger

logger = get_logger(__name__)


def mask_phone(phone: str) -> str:
    """
    脱敏手机号

    Args:
        phone: 手机号

    Returns:
        脱敏后的手机号
    """
    if not phone:
        return phone

    # 匹配中国大陆手机号
    pattern = r"1[3-9]\d{9}"
    match = re.search(pattern, phone)

    if match:
        original = match.group()
        masked = original[:3] + "****" + original[7:]
        return phone.replace(original, masked)

    return phone


def mask_id_number(id_number: str) -> str:
    """
    脱敏身份证号

    Args:
        id_number: 身份证号

    Returns:
        脱敏后的身份证号
    """
    if not id_number:
        return id_number

    # 匹配身份证号（18 位或 15 位）
    pattern = r"\d{17}[\dXx]|\d{15}"
    match = re.search(pattern, id_number)

    if match:
        original = match.group()
        if len(original) == 18:
            masked = original[:6] + "********" + original[14:]
        else:
            masked = original[:6] + "******" + original[12:]
        return id_number.replace(original, masked)

    return id_number


def mask_medical_record(medical_record: str) -> str:
    """
    脱敏病历号

    Args:
        medical_record: 病历号

    Returns:
        脱敏后的病历号
    """
    if not medical_record:
        return medical_record

    # 匹配常见病历号格式（字母 + 数字组合，长度 8-20）
    pattern = r"[A-Z]{1,3}\d{6,15}|[MZ]\d{8,12}"
    match = re.search(pattern, medical_record, re.IGNORECASE)

    if match:
        original = match.group()
        if len(original) > 8:
            masked = original[:4] + "*" * (len(original) - 8) + original[-4:]
        else:
            masked = original[:2] + "*" * (len(original) - 4) + original[-2:]
        return medical_record.replace(original, masked)

    return medical_record


def mask_sensitive_info(text: str) -> str:
    """
    脱敏所有敏感信息

    Args:
        text: 原始文本

    Returns:
        脱敏后的文本
    """
    if not text:
        return text

    # 依次脱敏
    text = mask_phone(text)
    text = mask_id_number(text)
    text = mask_medical_record(text)

    return text


def validate_api_key(
    provided_key: str, expected_key: str, header_name: str = "X-API-Key"
) -> bool:
    """
    验证 API Key

    Args:
        provided_key: 提供的 API Key
        expected_key: 期望的 API Key
        header_name: 请求头名称

    Returns:
        验证是否通过

    Raises:
        AuthenticationError: 鉴权失败
    """
    if not provided_key:
        logger.error(f"API Key 缺失，请求头：{header_name}")
        raise AuthenticationError(
            message="API Key 缺失",
            code="MISSING_API_KEY",
            details={"header": header_name},
        )

    # 使用恒定时间比较防止时序攻击
    provided_hash = hashlib.sha256(provided_key.encode()).digest()
    expected_hash = hashlib.sha256(expected_key.encode()).digest()

    if not _safe_compare(provided_hash, expected_hash):
        logger.error(f"API Key 验证失败，请求头：{header_name}")
        raise AuthenticationError(
            message="API Key 无效",
            code="INVALID_API_KEY",
            details={"header": header_name},
        )

    logger.debug("API Key 验证通过")
    return True


def _safe_compare(a: bytes, b: bytes) -> bool:
    """安全比较（防止时序攻击）"""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    return result == 0


class RateLimiter:
    """限流器"""

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        max_requests: int = 10,
        window_seconds: int = 60,
    ):
        """
        初始化限流器

        Args:
            redis_client: Redis 客户端
            max_requests: 最大请求数
            window_seconds: 时间窗口（秒）
        """
        self.redis_client = redis_client
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.logger = get_logger(__name__)

    def is_allowed(self, identifier: str) -> bool:
        """
        检查请求是否允许

        Args:
            identifier: 请求标识（如用户 ID、IP 等）

        Returns:
            是否允许

        Raises:
            RateLimitError: 超过限流
        """
        if not self.redis_client:
            # 无 Redis 时不限制
            return True

        try:
            key = f"rate_limit:{identifier}"
            current_time = int(time.time())
            window_start = current_time - self.window_seconds

            # 使用 Pipeline 提高性能
            pipe = self.redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {f"{current_time}:{time.time_ns()}": current_time})
            pipe.zcard(key)
            pipe.expire(key, self.window_seconds * 2)
            results = pipe.execute()

            request_count = results[2]

            if request_count > self.max_requests:
                self.logger.warning(
                    f"请求限流：{identifier}, 当前请求数：{request_count}, 限制：{self.max_requests}"
                )
                raise RateLimitError(
                    message=f"请求频率超限，请稍后重试",
                    code="RATE_LIMIT_EXCEEDED",
                    details={
                        "identifier": identifier,
                        "current_count": request_count,
                        "max_requests": self.max_requests,
                    },
                )

            return True

        except redis.RedisError as e:
            self.logger.error(f"Redis 限流检查失败：{e}")
            # Redis 故障时不限制（降级策略）
            return True

    def get_remaining(self, identifier: str) -> int:
        """
        获取剩余请求数

        Args:
            identifier: 请求标识

        Returns:
            剩余请求数
        """
        if not self.redis_client:
            return self.max_requests

        try:
            key = f"rate_limit:{identifier}"
            current_time = int(time.time())
            window_start = current_time - self.window_seconds

            self.redis_client.zremrangebyscore(key, 0, window_start)
            count = self.redis_client.zcard(key)

            return max(0, self.max_requests - count)

        except redis.RedisError as e:
            self.logger.error(f"Redis 查询剩余请求数失败：{e}")
            return self.max_requests


def rate_limit(
    max_requests: int = 10,
    window_seconds: int = 60,
    identifier_func: callable = None,
):
    """
    限流装饰器

    Args:
        max_requests: 最大请求数
        window_seconds: 时间窗口
        identifier_func: 获取请求标识的函数
    """

    def decorator(func):
        limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取请求标识
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)
            else:
                identifier = kwargs.get("user_id", "default")

            # 检查限流
            limiter.is_allowed(identifier)

            # 执行函数
            return func(*args, **kwargs)

        return wrapper

    return decorator
