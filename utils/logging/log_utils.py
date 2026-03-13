"""
日志工具模块
"""

import logging
from pathlib import Path
from loguru import logger
from datetime import datetime
import sys


def setup_logger(
    log_file: str = "logs/app.log",
    level: str = "INFO",
    max_size: str = "10 MB",
    backup_count: int = 7,
    format_string: str = None,
) -> None:
    """
    配置日志系统

    Args:
        log_file: 日志文件路径
        level: 日志级别
        max_size: 单个日志文件最大大小
        backup_count: 保留的日志文件数量
        format_string: 日志格式
    """
    # 移除默认处理器
    logger.remove()

    # 默认格式
    if format_string is None:
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # 控制台输出
    logger.add(
        sys.stderr,
        format=format_string,
        level=level,
        colorize=True,
    )

    # 文件输出（支持轮转）
    logger.add(
        log_file,
        format=format_string,
        level=level,
        rotation=max_size,
        retention=backup_count,
        compression="zip",
        encoding="utf-8",
    )

    # 错误日志单独文件
    error_log_file = Path(log_file).parent / f"error_{Path(log_file).name}"
    logger.add(
        error_log_file,
        format=format_string,
        level="ERROR",
        rotation=max_size,
        retention=backup_count,
        compression="zip",
        encoding="utf-8",
    )


def get_logger(name: str = __name__) -> logger:
    """
    获取日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        logger 实例
    """
    return logger.bind(name=name)


class LoggerAdapter:
    """日志适配器（用于标准 logging 库）"""

    def __init__(self, name: str = __name__):
        self.logger = get_logger(name)

    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs):
        self.logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self.logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, **kwargs)

    def exception(self, msg: str, **kwargs):
        self.logger.exception(msg, **kwargs)
