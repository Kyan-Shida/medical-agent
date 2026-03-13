"""
自定义异常模块
"""


class BaseMedicalAgentError(Exception):
    """医疗 Agent 基础异常类"""

    def __init__(self, message: str, code: str = "UNKNOWN_ERROR", details: dict = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }


class LLMCallError(BaseMedicalAgentError):
    """LLM 调用异常"""

    def __init__(self, message: str, code: str = "LLM_CALL_ERROR", details: dict = None):
        super().__init__(message, code, details)


class LLMTimeoutError(LLMCallError):
    """LLM 调用超时"""

    def __init__(self, message: str = "LLM 调用超时", code: str = "LLM_TIMEOUT", details: dict = None):
        super().__init__(message, code, details)


class LLMRateLimitError(LLMCallError):
    """LLM 请求限流"""

    def __init__(
        self, message: str = "LLM 请求频率超限", code: str = "LLM_RATE_LIMIT", details: dict = None
    ):
        super().__init__(message, code, details)


class RetrieveError(BaseMedicalAgentError):
    """检索异常"""

    def __init__(self, message: str, code: str = "RETRIEVE_ERROR", details: dict = None):
        super().__init__(message, code, details)


class VectorStoreError(RetrieveError):
    """向量库异常"""

    def __init__(self, message: str, code: str = "VECTOR_STORE_ERROR", details: dict = None):
        super().__init__(message, code, details)


class DocumentLoadError(RetrieveError):
    """文档加载异常"""

    def __init__(self, message: str, code: str = "DOCUMENT_LOAD_ERROR", details: dict = None):
        super().__init__(message, code, details)


class IntentClassificationError(BaseMedicalAgentError):
    """意图识别异常"""

    def __init__(
        self, message: str, code: str = "INTENT_CLASSIFICATION_ERROR", details: dict = None
    ):
        super().__init__(message, code, details)


class RateLimitError(BaseMedicalAgentError):
    """请求限流异常"""

    def __init__(self, message: str, code: str = "RATE_LIMIT_ERROR", details: dict = None):
        super().__init__(message, code, details)


class AuthenticationError(BaseMedicalAgentError):
    """鉴权失败异常"""

    def __init__(self, message: str, code: str = "AUTHENTICATION_ERROR", details: dict = None):
        super().__init__(message, code, details)


class ConfigError(BaseMedicalAgentError):
    """配置异常"""

    def __init__(self, message: str, code: str = "CONFIG_ERROR", details: dict = None):
        super().__init__(message, code, details)


class CacheError(BaseMedicalAgentError):
    """缓存异常"""

    def __init__(self, message: str, code: str = "CACHE_ERROR", details: dict = None):
        super().__init__(message, code, details)
