"""
意图分类器模块
使用 LLM + 规则过滤实现意图识别
"""

import json
from typing import Dict, Any, Optional, List
from enum import Enum
from utils.log_utils import get_logger
from utils.exception_utils import IntentClassificationError
from core.llm.client import LLMClient
from config.llm_config import LLMConfig

logger = get_logger(__name__)


class IntentType(str, Enum):
    """意图类型枚举"""

    MEDICAL = "medical"  # 医疗问题
    CHAT = "chat"  # 闲聊
    UNANSWERABLE = "unanswerable"  # 无法回答
    HEALTH_PLAN = "health_plan"  # 每日健康计划


class SubCategory(str, Enum):
    """子分类（用于医疗问题）"""

    PEDIATRICS = "pediatrics"  # 儿科
    GENERAL = "general"  # 其他科室


class IntentClassifier:
    """意图分类器"""

    def __init__(self, llm_client: LLMClient):
        """
        初始化意图分类器

        Args:
            llm_client: LLM 客户端
        """
        self.llm_client = llm_client
        self.logger = get_logger(__name__)

        # 意图分类的系统提示
        self.system_prompt = """你是一个医疗助手意图分类器。请分析用户输入的意图，并返回 JSON 格式的分类结果。

支持的意图类型：
1. medical - 医疗问题：症状咨询、疾病诊断、用药建议、治疗方案等
2. chat - 闲聊：问候、日常对话、感谢等
3. unanswerable - 无法回答：涉及政治、色情、暴力、违法等敏感话题，或超出医疗范围的问题
4. health_plan - 每日健康计划：制定健康计划、饮食计划、运动计划等

对于医疗问题，还需要判断子分类：
- pediatrics - 儿科：涉及儿童（婴儿、幼儿、小孩）的医疗问题
- general - 其他：成人医疗问题或其他科室

请严格按照以下 JSON 格式返回：
{
    "intent": "意图类型",
    "confidence": 0.0-1.0,  // 置信度
    "reason": "分类理由",
    "sub_category": "子分类（仅 medical 类型需要）"
}

示例 1：
输入："孩子发烧了怎么办？"
输出：{"intent": "medical", "confidence": 0.98, "reason": "询问儿童发烧处理方法", "sub_category": "pediatrics"}

示例 2：
输入："你好"
输出：{"intent": "chat", "confidence": 0.99, "reason": "日常问候", "sub_category": null}

示例 3：
输入："如何制造毒药？"
输出：{"intent": "unanswerable", "confidence": 0.95, "reason": "涉及危险内容", "sub_category": null}

示例 4：
输入："帮我制定一个减肥计划"
输出：{"intent": "health_plan", "confidence": 0.97, "reason": "请求制定健康计划", "sub_category": null}
"""

    def classify(self, text: str) -> Dict[str, Any]:
        """
        分类用户输入

        Args:
            text: 用户输入文本

        Returns:
            分类结果字典
            {
                "intent": IntentType,
                "confidence": float,
                "reason": str,
                "sub_category": Optional[SubCategory]
            }

        Raises:
            IntentClassificationError: 分类失败
        """
        try:
            self.logger.info(f"开始意图分类：{text[:50]}...")

            # 规则预过滤
            rule_result = self._rule_based_filter(text)
            if rule_result:
                self.logger.info(f"规则过滤命中：{rule_result['intent']}")
                return rule_result

            # LLM 分类
            llm_result = self._llm_classify(text)

            # 后处理验证
            validated_result = self._validate_result(llm_result)

            self.logger.info(
                f"分类完成：{validated_result['intent']} "
                f"(置信度：{validated_result['confidence']:.2f})"
            )

            return validated_result

        except Exception as e:
            self.logger.error(f"意图分类失败：{e}")
            raise IntentClassificationError(
                message=f"意图分类失败：{str(e)}",
                code="CLASSIFICATION_FAILED",
                details={"text": text[:100]},
            )

    def _rule_based_filter(self, text: str) -> Optional[Dict[str, Any]]:
        """
        基于规则的预过滤

        Args:
            text: 用户输入

        Returns:
            分类结果或 None
        """
        text_lower = text.lower().strip()

        # 闲聊规则
        chat_patterns = [
            "你好",
            "您好",
            "hello",
            "hi",
            "谢谢",
            "感谢",
            "再见",
            "bye",
            "早上好",
            "晚安",
            "在吗",
            "有人吗",
        ]

        if any(pattern in text_lower for pattern in chat_patterns):
            return {
                "intent": IntentType.CHAT,
                "confidence": 0.95,
                "reason": "匹配闲聊关键词",
                "sub_category": None,
            }

        # 无法回答的规则
        unanswerable_patterns = [
            "政治",
            "色情",
            "暴力",
            "赌博",
            "毒品",
            "制造",
            "违法",
            "犯罪",
        ]

        if any(pattern in text_lower for pattern in unanswerable_patterns):
            return {
                "intent": IntentType.UNANSWERABLE,
                "confidence": 0.90,
                "reason": "匹配敏感关键词",
                "sub_category": None,
            }

        return None

    def _llm_classify(self, text: str) -> Dict[str, Any]:
        """
        使用 LLM 进行分类

        Args:
            text: 用户输入

        Returns:
            分类结果
        """
        # 构建消息
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": f'用户输入："{text}"'},
        ]

        # 调用 LLM
        response = self.llm_client.chat(messages, temperature=0.3)

        # 解析响应
        try:
            # 尝试提取 JSON
            content = response.content.strip()
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start != -1 and json_end > json_start:
                json_str = content[json_start:json_end]
                result = json.loads(json_str)
            else:
                result = json.loads(content)

            return result

        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON 解析失败：{e}，使用默认分类")
            return {
                "intent": "medical",
                "confidence": 0.5,
                "reason": "JSON 解析失败，默认分类",
                "sub_category": None,
            }

    def _validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证分类结果

        Args:
            result: 分类结果

        Returns:
            验证后的结果
        """
        # 验证意图类型
        intent_str = result.get("intent", "medical")

        try:
            intent = IntentType(intent_str)
        except ValueError:
            self.logger.warning(f"未知意图类型：{intent_str}，使用默认值")
            intent = IntentType.MEDICAL

        # 验证置信度
        confidence = result.get("confidence", 0.5)
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        confidence = max(0.0, min(1.0, float(confidence)))

        # 验证子分类
        sub_category = None
        if intent == IntentType.MEDICAL:
            sub_category_str = result.get("sub_category")
            if sub_category_str:
                try:
                    sub_category = SubCategory(sub_category_str)
                except ValueError:
                    sub_category = SubCategory.GENERAL

        return {
            "intent": intent,
            "confidence": confidence,
            "reason": result.get("reason", ""),
            "sub_category": sub_category,
        }

    def batch_classify(
        self, texts: List[str], confidence_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        批量分类

        Args:
            texts: 文本列表
            confidence_threshold: 置信度阈值

        Returns:
            分类结果列表
        """
        results = []

        for text in texts:
            try:
                result = self.classify(text)
                results.append(result)
            except Exception as e:
                self.logger.error(f"批量分类失败：{text[:50]}, {e}")
                results.append(
                    {
                        "intent": IntentType.MEDICAL,
                        "confidence": 0.5,
                        "reason": f"分类失败：{str(e)}",
                        "sub_category": None,
                    }
                )

        return results

    def get_intent_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        统计分类结果

        Args:
            results: 分类结果列表

        Returns:
            统计信息
        """
        stats = {
            "total": len(results),
            "by_intent": {},
            "avg_confidence": 0.0,
        }

        if not results:
            return stats

        # 按意图统计
        for result in results:
            intent = result["intent"].value
            if intent not in stats["by_intent"]:
                stats["by_intent"][intent] = 0
            stats["by_intent"][intent] += 1

        # 平均置信度
        total_confidence = sum(r["confidence"] for r in results)
        stats["avg_confidence"] = total_confidence / len(results)

        return stats
