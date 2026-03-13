"""
增强的日志记录模�?提供结构化日志、性能追踪和上下文管理
"""

import time
import functools
import json
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
from utils.logging.log_utils import get_logger

logger = get_logger(__name__)


class PerformanceTracker:
    """性能追踪�?""

    def __init__(self, operation_name: str):
        """
        初始化性能追踪�?
        Args:
            operation_name: 操作名称
        """
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.metadata = {}

    def start(self):
        """开始追�?""
        self.start_time = time.time()
        logger.info(f"⏱️ 开始：{self.operation_name}")
        return self

    def stop(self):
        """停止追踪"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        logger.info(
            f"�?完成：{self.operation_name} - 耗时：{self.duration:.3f}�?
        )
        return self

    def add_metadata(self, **kwargs):
        """
        添加元数�?
        Args:
            **kwargs: 元数据键值对
        """
        self.metadata.update(kwargs)
        return self

    def get_report(self) -> Dict[str, Any]:
        """
        获取性能报告

        Returns:
            性能报告字典
        """
        return {
            "operation": self.operation_name,
            "duration_seconds": self.duration,
            "duration_ms": self.duration * 1000 if self.duration else None,
            "metadata": self.metadata,
        }

    def log_report(self, level: str = "info"):
        """
        记录性能报告

        Args:
            level: 日志级别
        """
        if self.duration:
            log_func = getattr(logger, level)
            log_func(
                f"📊 性能报告 - {self.operation_name}: "
                f"{self.duration * 1000:.2f}ms"
            )
            if self.metadata:
                log_func(f"元数据：{json.dumps(self.metadata, ensure_ascii=False)}")


def track_performance(operation_name: str = None, log_level: str = "info") -> Callable:
    """
    性能追踪装饰�?
    Args:
        operation_name: 操作名称
        log_level: 日志级别

    Returns:
        装饰�?    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            op_name = operation_name or func.__name__
            tracker = PerformanceTracker(op_name)

            try:
                tracker.start()
                result = func(*args, **kwargs)
                tracker.stop()
                tracker.log_report(log_level)
                return result
            except Exception as e:
                tracker.stop()
                tracker.add_metadata(error=str(e))
                tracker.log_report("error")
                raise

        return wrapper

    return decorator


@contextmanager
def performance_context(operation_name: str, log_level: str = "info"):
    """
    性能追踪上下文管理器

    Args:
        operation_name: 操作名称
        log_level: 日志级别

    Yields:
        PerformanceTracker 实例
    """
    tracker = PerformanceTracker(operation_name)
    try:
        tracker.start()
        yield tracker
        tracker.stop()
        tracker.log_report(log_level)
    except Exception as e:
        tracker.stop()
        tracker.add_metadata(error=str(e))
        tracker.log_report("error")
        raise


class StructuredLogger:
    """结构化日志记录器"""

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """
        初始化结构化日志记录�?
        Args:
            context: 初始上下�?        """
        self.context = context or {}
        self.logger = get_logger(__name__)

    def set_context(self, **kwargs):
        """
        设置上下�?
        Args:
            **kwargs: 上下文键值对
        """
        self.context.update(kwargs)
        return self

    def log(
        self,
        level: str,
        message: str,
        **kwargs,
    ) -> None:
        """
        记录结构化日�?
        Args:
            level: 日志级别
            message: 消息
            **kwargs: 额外字段
        """
        log_entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "context": self.context.copy(),
            "extra": kwargs,
        }

        log_func = getattr(self.logger, level, self.logger.info)
        log_func(json.dumps(log_entry, ensure_ascii=False))

    def info(self, message: str, **kwargs):
        """记录 INFO 级别日志"""
        self.log("info", message, **kwargs)

    def error(self, message: str, **kwargs):
        """记录 ERROR 级别日志"""
        self.log("error", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """记录 WARNING 级别日志"""
        self.log("warning", message, **kwargs)

    def debug(self, message: str, **kwargs):
        """记录 DEBUG 级别日志"""
        self.log("debug", message, **kwargs)


def log_function_call(include_args: bool = True, include_result: bool = False) -> Callable:
    """
    函数调用日志装饰�?
    Args:
        include_args: 是否记录参数
        include_result: 是否记录返回�?
    Returns:
        装饰�?    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            func_name = func.__name__

            # 记录参数
            if include_args:
                args_str = ", ".join([repr(a) for a in args[:3]])  # 只记录前 3 个参�?                kwargs_str = ", ".join([f"{k}={v}" for k, v in list(kwargs.items())[:3]])
                params = f"({args_str}, {kwargs_str})" if kwargs else f"({args_str})"
                logger.debug(f"📞 调用：{func_name}{params}")
            else:
                logger.debug(f"📞 调用：{func_name}")

            # 执行函数
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # 记录结果
                if include_result:
                    result_str = str(result)[:100]
                    logger.debug(f"�?返回：{func_name} - {result_str} (耗时：{duration * 1000:.2f}ms)")
                else:
                    logger.debug(f"�?完成：{func_name} (耗时：{duration * 1000:.2f}ms)")

                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"�?异常：{func_name} - {str(e)} (耗时：{duration * 1000:.2f}ms)")
                raise

        return wrapper

    return decorator


class LogLevel:
    """日志级别常量"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory:
    """日志分类常量"""

    LLM = "LLM"
    RAG = "RAG"
    INTENT = "INTENT"
    HANDLER = "HANDLER"
    WEB = "WEB"
    SYSTEM = "SYSTEM"
    USER = "USER"


def log_with_category(
    category: str,
    level: str = "info",
    include_stack: bool = False,
) -> Callable:
    """
    带分类的日志装饰�?
    Args:
        category: 日志分类
        level: 日志级别
        include_stack: 是否包含堆栈信息

    Returns:
        装饰�?    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            func_name = func.__name__

            # 构建日志消息
            message = f"[{category}] {func_name}"

            log_func = getattr(logger, level, logger.info)

            if include_stack:
                import traceback

                stack = traceback.format_stack()
                log_func(f"{message}\n{''.join(stack[-5:-1])}")
            else:
                log_func(message)

            return func(*args, **kwargs)

        return wrapper

    return decorator
