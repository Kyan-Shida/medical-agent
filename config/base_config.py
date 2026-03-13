"""
基础配置模块
"""

import os
from pathlib import Path
from dotenv import load_dotenv


class BaseConfig:
    """基础配置类"""

    def __init__(self, env_file: str = ".env.dev"):
        """
        初始化配置

        Args:
            env_file: 环境变量文件路径
        """
        # 项目路径
        self.PROJECT_ROOT = Path(__file__).parent.parent
        self.LOGS_DIR = self.PROJECT_ROOT / "logs"
        self.CACHE_DIR = self.PROJECT_ROOT / "cache"
        self.KNOWLEDGE_BASE_DIR = self.PROJECT_ROOT / "knowledge_base"

        # 加载环境变量
        self.env_file = env_file
        self.load_env()

        # 创建必要目录
        self._create_directories()

    def load_env(self) -> None:
        """加载环境变量"""
        env_path = self.PROJECT_ROOT / self.env_file
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
        else:
            load_dotenv()

    def _create_directories(self) -> None:
        """创建必要目录"""
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        self.KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: str = "") -> str:
        """
        获取环境变量值

        Args:
            key: 环境变量名
            default: 默认值

        Returns:
            环境变量值
        """
        return os.getenv(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数类型环境变量"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点类型环境变量"""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔类型环境变量"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "y")
