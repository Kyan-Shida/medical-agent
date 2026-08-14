"""
``响应解析工具集
LLM 响应解析模块：
对 LLM 返回的原始结果做结构化解析（如提取 JSON、分类结果、业务字段），屏蔽不同模型的返回格式差异
"""

import json
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from utils.exception_utils import LLMCallError
from utils.log_utils import get_logger

logger = get_logger(__name__)


@dataclass
class ParsedResponse:
    """定义解析后的响应类型"""

    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    raw_response: Dict[str, Any]
    is_valid: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "total_tokens": self.total_tokens,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "is_valid": self.is_valid,
            "error_message": self.error_message,
        }


class ResponseParser:
    """LLM 响应解析器"""

    def __init__(self):
        self.logger = get_logger(__name__)

    def parse(self, response_data: Dict[str, Any]) -> ParsedResponse:
        """
        解析 LLM API 响应

        Args:
            response_data: API 响应数据

        Returns:
            解析后的响应

        Raises:
            LLMCallError: 解析失败
        """
        try:
            # 检查响应结构
            if not response_data:
                raise LLMCallError("响应数据为空", code="EMPTY_RESPONSE")

            # 提取 choices
            choices = response_data.get("choices", [])
            if not choices or len(choices) == 0:
                raise LLMCallError("响应中无 choices", code="NO_CHOICES")

            # 提取第一个 choice
            choice = choices[0]
            message = choice.get("message", {})
            content = message.get("content", "")

            # 提取 usage 信息
            usage = response_data.get("usage", {})
            finish_reason = choice.get("finish_reason", "unknown")

            # 提取模型信息
            model = response_data.get("model", "unknown")

            # 验证响应内容
            is_valid, error_message = self._validate_response(content, finish_reason)

            parsed = ParsedResponse(
                content=content or "",
                model=model,
                usage=usage,
                finish_reason=finish_reason,
                total_tokens=usage.get("total_tokens", 0),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                raw_response=response_data,
                is_valid=is_valid,
                error_message=error_message,
            )

            self.logger.debug(f"响应解析成功：{len(content)} 字符")
            return parsed

        except LLMCallError:
            raise
        except Exception as e:
            self.logger.error(f"响应解析失败：{e}")
            raise LLMCallError(
                message=f"响应解析失败：{str(e)}",
                code="PARSE_ERROR",
                details={"response": str(response_data)[:500]},
            )

    def _validate_response(
        self, content: str, finish_reason: str
    ) -> tuple[bool, Optional[str]]:
        """
        验证响应有效性

        Args:
            content: 响应内容
            finish_reason: 结束原因

        Returns:
            (是否有效，错误信息)
        """
        # 检查内容是否为空
        if not content or len(content.strip()) == 0:
            return False, "响应内容为空"

        # 检查结束原因
        if finish_reason not in ["stop", "length"]:
            self.logger.warning(f"非正常结束：{finish_reason}")
            if finish_reason == "content_filter":
                return False, "内容被过滤"
            elif finish_reason == "function_call":
                return False, "意外的函数调用"

        # 检查内容是否被截断
        if finish_reason == "length":
            self.logger.warning("响应可能被截断")
            return True, None  # 截断的响应仍然可用

        return True, None

    def parse_json_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析 JSON 格式的响应

        Args:
            response_data: API 响应数据

        Returns:
            解析后的 JSON 对象

        Raises:
            LLMCallError: 解析失败
        """
        parsed = self.parse(response_data)  #先转ParsedResponse格式
        content = parsed.content.strip()

        # 尝试提取 JSON（处理可能的 markdown 包裹）
        json_content = self._extract_json(content)

        try:
            return json.loads(json_content)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 解析失败：{e}, 内容：{content[:200]}")
            raise LLMCallError(
                message=f"JSON 格式解析失败：{str(e)}",
                code="JSON_PARSE_ERROR",
                details={"content": content[:500]},
            )

    def _extract_json(self, content: str) -> str:
        """
        从内容中提取 JSON 字符串

        Args:
            content: 原始内容

        Returns:
            JSON 字符串
        """
        content = content.strip()

        # 处理 markdown 代码块
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        # 尝试查找第一个 { 和最后一个 }
        start_idx = content.find("{")
        end_idx = content.rfind("}")

        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            return content[start_idx : end_idx + 1]

        return content

    def parse_intent_classification(
        self, response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析意图分类响应

        Args:
            response_data: API 响应数据

        Returns:
            意图分类结果
        """
        try:
            result = self.parse_json_response(response_data)

            # 验证必需字段
            if "intent" not in result:
                raise LLMCallError("意图分类结果缺少 intent 字段", code="MISSING_INTENT")

            return {
                "intent": result["intent"],
                "confidence": result.get("confidence", 1.0),
                "reason": result.get("reason", ""),
                "sub_category": result.get("sub_category", None),
            }

        except LLMCallError:
            raise
        except Exception as e:
            self.logger.error(f"意图分类解析失败：{e}")
            raise LLMCallError(
                message=f"意图分类解析失败：{str(e)}",
                code="INTENT_PARSE_ERROR",
                details={"response": str(response_data)[:500]},
            )
