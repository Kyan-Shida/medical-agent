"""
LLM 客户端模块（原生 API 调用）
"""

import requests
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from config.llm_config import LLMConfig
from utils.log_utils import get_logger
from utils.exception_utils import LLMCallError, LLMTimeoutError, LLMRateLimitError
from utils.retry_utils import retry_with_backoff
from core.llm.parser import ResponseParser, ParsedResponse

logger = get_logger(__name__)


class LLMClient:
    """LLM API 客户端"""

    def __init__(self, config: LLMConfig):
        """
        初始化 LLM 客户端

        Args:
            config: LLM 配置
        """
        self.config = config
        self.parser = ResponseParser()
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        self.session.headers.update(config.get_api_headers())

        # 统计信息
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_time": 0.0,
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs,
    ) -> ParsedResponse:
        """
        聊天接口

        Args:
            messages: 消息列表 [{"role": "user", "content": "hello"}]
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式输出
            **kwargs: 其他参数

        Returns:
            解析后的响应

        Raises:
            LLMCallError: 调用失败
        """
        start_time = time.time()
        self.stats["total_requests"] += 1

        try:
            # 构建请求体
            payload = self._build_payload(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
                **kwargs,
            )

            # 发送请求
            response = self._send_request(payload)

            # 解析响应
            parsed_response = self.parser.parse(response)

            # 更新统计
            elapsed_time = time.time() - start_time
            self._update_stats(success=True, tokens=parsed_response.total_tokens, time=elapsed_time)

            self.logger.info(
                f"LLM 调用成功：{parsed_response.total_tokens} tokens, "
                f"耗时 {elapsed_time:.2f}s"
            )

            return parsed_response

        except LLMCallError:
            self._update_stats(success=False)
            raise
        except Exception as e:
            self._update_stats(success=False)
            self.logger.error(f"LLM 调用失败：{e}")
            raise LLMCallError(
                message=f"LLM 调用失败：{str(e)}",
                code="LLM_CALL_FAILED",
                details={"elapsed_time": time.time() - start_time},
            )

    @retry_with_backoff(
        max_retries=3,
        base_delay=1.0,
        exponential=True,
        jitter=True,
        exceptions=(LLMCallError, LLMTimeoutError, requests.exceptions.RequestException),
    )
    def _send_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送 API 请求（带重试）

        Args:
            payload: 请求体

        Returns:
            API 响应

        Raises:
            LLMTimeoutError: 请求超时
            LLMRateLimitError: 请求限流
            LLMCallError: 其他错误
        """
        url = f"{self.config.base_url}/chat/completions"

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.config.timeout,
            )

            # 处理响应状态码
            if response.status_code == 429:
                raise LLMRateLimitError(
                    message="API 请求频率超限",
                    code="API_RATE_LIMIT",
                    details={"status_code": 429},
                )

            if response.status_code == 401:
                raise LLMCallError(
                    message="API Key 无效",
                    code="INVALID_API_KEY",
                    details={"status_code": 401},
                )

            if response.status_code == 503:
                raise LLMCallError(
                    message="服务暂时不可用",
                    code="SERVICE_UNAVAILABLE",
                    details={"status_code": 503},
                )

            if response.status_code != 200:
                raise LLMCallError(
                    message=f"API 请求失败：{response.status_code}",
                    code="API_ERROR",
                    details={
                        "status_code": response.status_code,
                        "response": response.text[:500],
                    },
                )

            # 解析 JSON 响应
            try:
                return response.json()
            except json.JSONDecodeError as e:
                raise LLMCallError(
                    message=f"响应 JSON 解析失败：{str(e)}",
                    code="JSON_PARSE_ERROR",
                    details={"response": response.text[:500]},
                )

        except requests.exceptions.Timeout:
            raise LLMTimeoutError(
                message=f"请求超时（>{self.config.timeout}s）",
                code="REQUEST_TIMEOUT",
            )
        except requests.exceptions.ConnectionError as e:
            raise LLMCallError(
                message=f"网络连接失败：{str(e)}",
                code="CONNECTION_ERROR",
            )
        except requests.exceptions.RequestException as e:
            raise LLMCallError(
                message=f"请求异常：{str(e)}",
                code="REQUEST_ERROR",
            )

    def _build_payload(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float],
        max_tokens: Optional[int],
        stream: bool,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        构建请求体

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式
            **kwargs: 其他参数

        Returns:
            请求体字典
        """
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": stream,
        }

        # 添加可选参数
        if temperature is not None:
            payload["temperature"] = temperature
        else:
            payload["temperature"] = self.config.temperature

        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        else:
            payload["max_tokens"] = self.config.max_tokens

        # 添加其他参数
        payload.update(kwargs)

        self.logger.debug(f"请求参数：{payload}")
        return payload

    def _update_stats(self, success: bool, tokens: int = 0, time: float = 0.0) -> None:
        """更新统计信息"""
        self.stats["total_requests"] += 1
        if success:
            self.stats["successful_requests"] += 1
            self.stats["total_tokens"] += tokens
            self.stats["total_time"] += time
        else:
            self.stats["failed_requests"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats["success_rate"] = (
            stats["successful_requests"] / stats["total_requests"]
            if stats["total_requests"] > 0
            else 0.0
        )
        stats["avg_time"] = (
            stats["total_time"] / stats["successful_requests"]
            if stats["successful_requests"] > 0
            else 0.0
        )
        stats["avg_tokens"] = (
            stats["total_tokens"] / stats["successful_requests"]
            if stats["successful_requests"] > 0
            else 0.0
        )
        return stats

    def simple_chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        简单聊天接口

        Args:
            prompt: 用户输入
            system_prompt: 系统提示

        Returns:
            AI 回复内容
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.chat(messages)
        return response.content

    def test_connection(self) -> bool:
        """
        测试 API 连接

        Returns:
            连接是否成功
        """
        try:
            messages = [{"role": "user", "content": "Hello"}]
            response = self.chat(messages)
            return response.is_valid
        except Exception as e:
            self.logger.error(f"连接测试失败：{e}")
            return False
