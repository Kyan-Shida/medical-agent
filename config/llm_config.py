"""
LLM 配置模块
"""

from pydantic import BaseModel, Field
from typing import Optional
from config.base_config import BaseConfig


class LLMConfig(BaseModel):
    """LLM 配置类"""

    # API 配置
    api_key: str = Field(default="", description="LLM API 密钥")
    base_url: str = Field(default="https://open.bigmodel.cn/api/paas/v4", description="API 基础 URL")
    model: str = Field(default="glm-4-flash", description="模型名称")

    # 请求参数
    max_tokens: int = Field(default=2048, description="最大生成 token 数", ge=1, le=32000)
    temperature: float = Field(default=0.7, description="温度参数", ge=0.0, le=2.0)
    timeout: int = Field(default=30, description="请求超时时间 (秒)", ge=1, le=300)

    # 重试配置
    max_retries: int = Field(default=3, description="最大重试次数", ge=0, le=10)
    retry_delay: float = Field(default=1.0, description="重试延迟 (秒)", ge=0.0, le=10.0)
    exponential_backoff: bool = Field(default=True, description="是否启用指数退避")

    # 降级配置
    fallback_model: Optional[str] = Field(default=None, description="降级模型")
    enable_fallback: bool = Field(default=True, description="是否启用降级")

    # 缓存配置
    enable_cache: bool = Field(default=True, description="是否启用响应缓存")
    cache_ttl: int = Field(default=3600, description="缓存 TTL(秒)")

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_env(cls, config: BaseConfig) -> "LLMConfig":
        """
        从环境变量加载配置

        Args:
            config: 基础配置对象

        Returns:
            LLMConfig 实例
        """
        return cls(
            api_key=config.get("LLM_API_KEY", ""),
            base_url=config.get("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
            model=config.get("LLM_MODEL", "glm-4-flash"),
            max_tokens=config.get_int("LLM_MAX_TOKENS", 2048),
            temperature=config.get_float("LLM_TEMPERATURE", 0.7),
            timeout=config.get_int("LLM_TIMEOUT", 30),
            max_retries=config.get_int("LLM_MAX_RETRIES", 3),
            retry_delay=config.get_float("LLM_RETRY_DELAY", 1.0),
            exponential_backoff=config.get_bool("LLM_EXPONENTIAL_BACKOFF", True),
            fallback_model=config.get("LLM_FALLBACK_MODEL", None),
            enable_fallback=config.get_bool("LLM_ENABLE_FALLBACK", True),
            enable_cache=config.get_bool("LLM_ENABLE_CACHE", True),
            cache_ttl=config.get_int("LLM_CACHE_TTL", 3600),
        )

    def validate(self) -> bool:
        """
        验证配置有效性

        Returns:
            配置是否有效
        """
        if not self.api_key or len(self.api_key.strip()) == 0:
            return False
        if not self.base_url or len(self.base_url.strip()) == 0:
            return False
        if not self.model or len(self.model.strip()) == 0:
            return False
        return True

    def get_api_headers(self) -> dict:
        """
        获取 API 请求头

        Returns:
            请求头字典
        """
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
