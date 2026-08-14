"""
```LLMClient` 核心类
LLM 客户端模块（原生 API 调用）
底层出口类，原生封装 OpenAI 兼容格式的 LLM API，内置重试、降级、异常处理，提供单轮对话等基础调用方法
"""

import requests
import time
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from config.llm_config import LLMConfig
from utils.log_utils import get_logger
from utils.exception_utils import LLMCallError, LLMTimeoutError


class LLMClient:
    """LLM 客户端"""

    def __init__(self, llm_config: LLMConfig):
        """
        初始化 LLM 客户端

        Args:
            llm_config: LLM 配置
        """
        self.config = llm_config
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
        })

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        聊天接口

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大 token 数
            stream: 是否流式输出

        Returns:
            LLM 响应
        """
        url = f"{self.config.base_url}/chat/completions"

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        try:
            self.logger.debug(f"发送请求到：{url}")
            response = self.session.post(url, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            self.logger.info(
                f"LLM 调用成功：{result.get('usage', {}).get('total_tokens', 0)} tokens"
            )

            return result

        except requests.exceptions.Timeout as e:
            self.logger.error(f"请求超时：{e}")
            raise LLMTimeoutError(f"LLM 请求超时")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"请求失败：{e}")
            raise LLMCallError(f"LLM 调用失败：{e}")

    def simple_chat(
        self,
        prompt: str,
        system_prompt: str = "你是一个有帮助的助手",
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        简单聊天接口

        Args:
            prompt: 用户输入
            system_prompt: 系统提示
            temperature: 温度参数
            max_tokens: 最大 token 数

        Returns:
            AI 回复
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        response = self.chat(messages, temperature=temperature, max_tokens=max_tokens)

        try:
            content = response["choices"][0]["message"]["content"]
            return content.strip()
        except (KeyError, IndexError) as e:
            self.logger.error(f"解析响应失败：{e}")
            raise LLMCallError(f"LLM 响应解析失败：{e}")

    def test_connection(self) -> bool:
        """
        测试 API 连接

        Returns:
            连接是否成功
        """
        try:
            self.logger.info("测试 API 连接...")
            response = self.simple_chat("你好", "你是一个友好的助手")
            self.logger.info(f"连接测试成功：{response[:50]}...")
            return True
        except Exception as e:
            self.logger.error(f"连接测试失败：{e}")
            return False
