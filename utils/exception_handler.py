"""
增强的异常处理模块
提供统一的异常捕获、日志记录和错误响应
"""

import traceback
import functools
from typing import Callable, Optional, Dict, Any, Type
from utils.log_utils import get_logger
from utils.exception_utils import BaseMedicalAgentError

logger = get_logger(__name__)


class ExceptionHandler:
    """异常处理器"""

    def __init__(self, default_error_message: str = "系统内部错误"):
        """
        初始化异常处理器

        Args:
            default_error_message: 默认错误消息
        """
        self.default_error_message = default_error_message
        self.logger = get_logger(__name__)

    def handle(self, func: Callable) -> Callable:
        """
        装饰器：捕获并记录异常

        Args:
            func: 被装饰的函数

        Returns:
            包装后的函数
        """

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                self.logger.info(f"开始执行：{func.__name__}")
                result = func(*args, **kwargs)
                self.logger.info(f"执行成功：{func.__name__}")
                return result
            except BaseMedicalAgentError as e:
                # 已知的业务异常
                self.logger.error(f"业务异常 - {func.__name__}: {e.code} - {e.message}")
                self._log_exception_details(e)
                # 重新抛出，让上层处理
                raise
            except Exception as e:
                # 未知异常
                error_msg = getattr(e, "message", str(e))
                self.logger.error(f"未知异常 - {func.__name__}: {error_msg}")
                self._log_exception_details(e)

                # 包装为通用异常
                raise BaseMedicalAgentError(
                    message=self.default_error_message,
                    code="INTERNAL_ERROR",
                    details={
                        "original_error": str(e),
                        "function": func.__name__,
                        "traceback": traceback.format_exc(),
                    },
                )

        return wrapper

    def _log_exception_details(self, exception: Exception) -> None:
        """
        记录异常详细信息

        Args:
            exception: 异常对象
        """
        self.logger.error("=" * 80)
        self.logger.error("异常详细信息:")
        self.logger.error(f"类型：{type(exception).__name__}")
        self.logger.error(f"消息：{str(exception)}")

        if hasattr(exception, "code"):
            self.logger.error(f"错误代码：{exception.code}")

        if hasattr(exception, "details") and exception.details:
            self.logger.error("详细信息:")
            for key, value in exception.details.items():
                self.logger.error(f"  {key}: {value}")

        # 完整堆栈跟踪
        self.logger.error("堆栈跟踪:")
        self.logger.error(traceback.format_exc())
        self.logger.error("=" * 80)


def handle_exception(
    default_message: str = None,
    error_codes: Optional[Dict[Type[Exception], str]] = None,
    log_level: str = "error",
) -> Callable:
    """
    异常处理装饰器工厂

    Args:
        default_message: 默认错误消息
        error_codes: 异常类型到错误代码的映射
        log_level: 日志级别

    Returns:
        装饰器
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                logger.info(f"开始执行：{func.__name__}")
                result = func(*args, **kwargs)
                logger.info(f"执行成功：{func.__name__}")
                return result
            except BaseMedicalAgentError as e:
                # 已知的业务异常
                getattr(logger, log_level)(f"业务异常 - {func.__name__}: {e.code} - {e.message}")
                raise
            except Exception as e:
                # 未知异常
                error_msg = default_message or f"系统错误：{str(e)}"
                error_code = "INTERNAL_ERROR"

                # 检查是否有特定的错误代码映射
                if error_codes:
                    for exc_type, code in error_codes.items():
                        if isinstance(e, exc_type):
                            error_code = code
                            break

                logger.error(f"异常 - {func.__name__}: {error_code} - {str(e)}")
                logger.error(traceback.format_exc())

                # 包装异常
                raise BaseMedicalAgentError(
                    message=error_msg,
                    code=error_code,
                    details={
                        "original_error": str(e),
                        "function": func.__name__,
                        "args": str(args)[:100],
                        "kwargs": str(kwargs)[:100],
                    },
                )

        return wrapper

    return decorator


def create_error_response(
    error: BaseMedicalAgentError,
    include_traceback: bool = False,
) -> Dict[str, Any]:
    """
    创建错误响应

    Args:
        error: 异常对象
        include_traceback: 是否包含堆栈跟踪

    Returns:
        错误响应字典
    """
    response = {
        "success": False,
        "error": {
            "type": type(error).__name__,
            "message": error.message,
            "code": error.code,
        },
    }

    if error.details:
        response["error"]["details"] = error.details

    if include_traceback:
        response["error"]["traceback"] = traceback.format_exc()

    return response


def safe_execute(
    func: Callable,
    *args,
    default_value: Any = None,
    on_error: Optional[Callable] = None,
    **kwargs,
) -> Any:
    """
    安全执行函数（捕获所有异常）

    Args:
        func: 要执行的函数
        *args: 函数参数
        default_value: 失败时的默认值
        on_error: 错误回调函数
        **kwargs: 函数关键字参数

    Returns:
        函数执行结果或默认值
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"安全执行失败 - {func.__name__}: {str(e)}")
        logger.error(traceback.format_exc())

        # 调用错误回调
        if on_error:
            try:
                on_error(e)
            except Exception as callback_error:
                logger.error(f"错误回调执行失败：{callback_error}")

        # 返回默认值
        return default_value
