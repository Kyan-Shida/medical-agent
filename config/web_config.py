"""
Web 面板配置模块
"""

from pydantic import BaseModel, Field
from config.base_config import BaseConfig


class WebConfig(BaseModel):
    """Web 面板配置类"""

    # 服务配置
    host: str = Field(default="0.0.0.0", description="服务主机")
    port: int = Field(default=8501, description="Web 服务端口", ge=1000, le=65535)
    web_port: int = Field(default=8501, description="Streamlit 端口")

    # 主题配置
    theme: str = Field(default="light", description="界面主题")
    show_sidebar: bool = Field(default=True, description="是否显示侧边栏")

    # 测试报告配置
    report_dir: str = Field(default="web/report", description="测试报告目录")
    enable_html_report: bool = Field(default=True, description="是否生成 HTML 报告")
    enable_json_report: bool = Field(default=True, description="是否生成 JSON 报告")

    # 会话配置
    session_timeout: int = Field(default=3600, description="会话超时时间 (秒)")
    max_session_count: int = Field(default=100, description="最大会话数")

    # 日志显示
    show_logs: bool = Field(default=True, description="是否显示日志")
    log_level: str = Field(default="INFO", description="日志级别")

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_env(cls, config: BaseConfig) -> "WebConfig":
        """从环境变量加载配置"""
        return cls(
            host=config.get("HOST", "0.0.0.0"),
            port=config.get_int("PORT", 8000),
            web_port=config.get_int("WEB_PORT", 8501),
            theme=config.get("WEB_THEME", "light"),
            show_sidebar=config.get_bool("WEB_SHOW_SIDEBAR", True),
            report_dir=config.get("WEB_REPORT_DIR", "web/report"),
            enable_html_report=config.get_bool("WEB_ENABLE_HTML_REPORT", True),
            enable_json_report=config.get_bool("WEB_ENABLE_JSON_REPORT", True),
            session_timeout=config.get_int("WEB_SESSION_TIMEOUT", 3600),
            max_session_count=config.get_int("WEB_MAX_SESSION_COUNT", 100),
            show_logs=config.get_bool("WEB_SHOW_LOGS", True),
            log_level=config.get("LOG_LEVEL", "INFO"),
        )
