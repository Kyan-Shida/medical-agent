"""
重试工具模块
"""

import time
import random
from typing import Callable, Any, Optional, Tuple
from functools import wraps
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryCallState,
)
from utils.log_utils import get_logger
from utils.exception_utils import LLMCallError, LLMTimeoutError

logger = get_logger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True,
    jitter: bool = True,
    exceptions: Tuple = (LLMCallError, LLMTimeoutError),
):
    """
    带指数退避的重试装饰器

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential: 是否使用指数退避
        jitter: 是否添加随机抖动
        exceptions: 需要重试的异常类型

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"重试达到最大次数 {max_retries}, 最后错误：{e}",
                            function=func.__name__,
                        )
                        raise

                    # 计算延迟
                    if exponential:
                        delay = base_delay * (2**attempt)
                    else:
                        delay = base_delay

                    # 添加抖动
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    # 限制最大延迟
                    delay = min(delay, max_delay)

                    logger.warning(
                        f"调用失败，{delay:.2f}秒后重试 (尝试 {attempt + 1}/{max_retries}): {e}",
                        function=func.__name__,
                    )

                    time.sleep(delay)

            # 理论上不会到达这里
            raise last_exception

        return wrapper

    return decorator


class TenacityRetry:
    """使用 tenacity 库的高级重试类"""

    @staticmethod
    def create(
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: Tuple = (LLMCallError, LLMTimeoutError),
    ):
        """
        创建重试装饰器

        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟
            max_delay: 最大延迟
            exceptions: 重试异常类型

        Returns:
            tenacity 重试装饰器
        """

        def on_retry(retry_state: RetryCallState):
            """重试回调"""
            logger.warning(
                f"重试中：{retry_state.fn.__name__}, "
                f"尝试 {retry_state.attempt_number}, "
                f"原因：{retry_state.outcome.exception()}"
            )

        return retry(
            stop=stop_after_attempt(max_retries),
            wait=wait_exponential(multiplier=base_delay, min=base_delay, max=max_delay),
            retry=retry_if_exception_type(exceptions),
            after=on_retry,
            reraise=True,
        )


def retry_request(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    exceptions: Tuple = (Exception,),
) -> Any:
    """
    对函数执行重试调用

    Args:
        func: 要执行的函数
        max_retries: 最大重试次数
        base_delay: 基础延迟
        exceptions: 需要捕获的异常

    Returns:
        函数执行结果

    Raises:
        最后一次异常
    """
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return func()

        except exceptions as e:
            last_exception = e

            if attempt == max_retries:
                raise

            delay = base_delay * (2**attempt)
            jitter_delay = delay * (0.5 + random.random())

            logger.warning(
                f"重试 {attempt + 1}/{max_retries}, 延迟 {jitter_delay:.2f}s: {e}",
                function=func.__name__,
            )

            time.sleep(jitter_delay)

    raise last_exception
