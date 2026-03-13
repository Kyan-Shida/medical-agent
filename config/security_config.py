"""
安全配置模块
"""

from pydantic import BaseModel, Field
from config.base_config import BaseConfig


class SecurityConfig(BaseModel):
    """安全配置类"""

    # 限流配置
    rate_limit_per_minute: int = Field(default=10, description="每分钟请求限制", ge=1, le=1000)
    rate_limit_window: int = Field(default=60, description="限流时间窗口 (秒)")

    # 数据保留
    data_retention_days: int = Field(default=7, description="数据保留天数", ge=1, le=365)

    # 鉴权配置
    api_key_header: str = Field(default="X-API-Key", description="API Key 请求头")
    enable_auth: bool = Field(default=True, description="是否启用鉴权")

    # 脱敏配置
    enable_masking: bool = Field(default=True, description="是否启用数据脱敏")
    mask_phone: bool = Field(default=True, description="脱敏手机号")
    mask_id_number: bool = Field(default=True, description="脱敏身份证号")
    mask_medical_record: bool = Field(default=True, description="脱敏病历号")

    # 输入限制
    max_input_length: int = Field(default=4000, description="最大输入长度", ge=100, le=10000)
    enable_input_filter: bool = Field(default=True, description="是否启用输入过滤")

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_env(cls, config: BaseConfig) -> "SecurityConfig":
        """从环境变量加载配置"""
        return cls(
            rate_limit_per_minute=config.get_int("RATE_LIMIT_PER_MINUTE", 10),
            rate_limit_window=config.get_int("RATE_LIMIT_WINDOW", 60),
            data_retention_days=config.get_int("DATA_RETENTION_DAYS", 7),
            api_key_header=config.get("API_KEY_HEADER", "X-API-Key"),
            enable_auth=config.get_bool("ENABLE_AUTH", True),
            enable_masking=config.get_bool("ENABLE_MASKING", True),
            mask_phone=config.get_bool("MASK_PHONE", True),
            mask_id_number=config.get_bool("MASK_ID_NUMBER", True),
            mask_medical_record=config.get_bool("MASK_MEDICAL_RECORD", True),
            max_input_length=config.get_int("MAX_INPUT_LENGTH", 4000),
            enable_input_filter=config.get_bool("ENABLE_INPUT_FILTER", True),
        )
