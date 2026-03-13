"""
意图识别模块测试
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from core.llm.client import LLMClient
from core.intent.classifier import IntentClassifier, IntentType, SubCategory
from core.intent.router import IntentRouter


class TestIntentType:
    """测试意图类型枚举"""

    def test_intent_type_values(self):
        """测试意图类型值"""
        assert IntentType.MEDICAL.value == "medical"
        assert IntentType.CHAT.value == "chat"
        assert IntentType.UNANSWERABLE.value == "unanswerable"
        assert IntentType.HEALTH_PLAN.value == "health_plan"

    def test_sub_category_values(self):
        """测试子分类值"""
        assert SubCategory.PEDIATRICS.value == "pediatrics"
        assert SubCategory.GENERAL.value == "general"


class TestIntentClassifier:
    """测试意图分类器"""

    @pytest.fixture
    def classifier(self):
        """创建分类器"""
        config = BaseConfig(env_file=".env.dev")
        llm_config = LLMConfig.from_env(config)
        llm_client = LLMClient(llm_config)
        return IntentClassifier(llm_client)

    def test_classify_medical_child_fever(self, classifier):
        """测试医疗问题 - 儿童发烧"""
        result = classifier.classify("孩子发烧了怎么办？")

        assert result["intent"] == IntentType.MEDICAL
        assert result["confidence"] > 0.5
        assert result["sub_category"] == SubCategory.PEDIATRICS
        assert "儿童" in result["reason"] or "发烧" in result["reason"]

    def test_classify_medical_adult_cold(self, classifier):
        """测试医疗问题 - 成人感冒"""
        result = classifier.classify("成人感冒吃什么药？")

        assert result["intent"] == IntentType.MEDICAL
        assert result["confidence"] > 0.5
        assert result["sub_category"] == SubCategory.GENERAL

    def test_classify_chat_greeting(self, classifier):
        """测试闲聊 - 问候"""
        result = classifier.classify("你好")

        assert result["intent"] == IntentType.CHAT
        assert result["confidence"] > 0.9
        assert result["sub_category"] is None

    def test_classify_chat_thanks(self, classifier):
        """测试闲聊 - 感谢"""
        result = classifier.classify("谢谢")

        assert result["intent"] == IntentType.CHAT
        assert result["confidence"] > 0.9

    def test_classify_unanswerable_dangerous(self, classifier):
        """测试无法回答 - 危险内容"""
        result = classifier.classify("如何制造毒药？")

        assert result["intent"] == IntentType.UNANSWERABLE
        assert result["confidence"] > 0.5

    def test_classify_health_plan_weight_loss(self, classifier):
        """测试健康计划 - 减肥"""
        result = classifier.classify("帮我制定一个减肥计划")

        assert result["intent"] == IntentType.HEALTH_PLAN
        assert result["confidence"] > 0.5
        assert result["sub_category"] is None

    def test_classify_with_low_confidence(self, classifier):
        """测试低置信度分类"""
        # 模糊的问题
        result = classifier.classify("那个...就是...")

        # 应该能分类，但置信度可能较低
        assert "intent" in result
        assert "confidence" in result

    def test_rule_based_filter_hello(self, classifier):
        """测试规则过滤 - 问候"""
        result = classifier._rule_based_filter("你好")

        assert result is not None
        assert result["intent"] == IntentType.CHAT
        assert result["confidence"] == 0.95

    def test_rule_based_filter_thanks(self, classifier):
        """测试规则过滤 - 感谢"""
        result = classifier._rule_based_filter("非常感谢")

        assert result is not None
        assert result["intent"] == IntentType.CHAT

    def test_rule_based_filter_sensitive(self, classifier):
        """测试规则过滤 - 敏感词"""
        result = classifier._rule_based_filter("涉及政治的问题")

        assert result is not None
        assert result["intent"] == IntentType.UNANSWERABLE

    def test_validate_result_valid(self, classifier):
        """测试验证结果 - 有效"""
        result = {
            "intent": "medical",
            "confidence": 0.95,
            "reason": "测试",
            "sub_category": "pediatrics",
        }

        validated = classifier._validate_result(result)

        assert validated["intent"] == IntentType.MEDICAL
        assert validated["confidence"] == 0.95
        assert validated["sub_category"] == SubCategory.PEDIATRICS

    def test_validate_result_invalid_intent(self, classifier):
        """测试验证结果 - 无效意图"""
        result = {
            "intent": "unknown",
            "confidence": 0.95,
            "reason": "测试",
            "sub_category": None,
        }

        validated = classifier._validate_result(result)

        assert validated["intent"] == IntentType.MEDICAL  # 默认值
        assert validated["confidence"] == 0.95

    def test_validate_result_invalid_confidence(self, classifier):
        """测试验证结果 - 无效置信度"""
        result = {
            "intent": "medical",
            "confidence": "invalid",
            "reason": "测试",
            "sub_category": None,
        }

        validated = classifier._validate_result(result)

        assert validated["confidence"] == 0.5  # 默认值

    def test_validate_result_confidence_range(self, classifier):
        """测试验证结果 - 置信度范围"""
        result = {
            "intent": "medical",
            "confidence": 1.5,  # 超出范围
            "reason": "测试",
            "sub_category": None,
        }

        validated = classifier._validate_result(result)

        assert 0.0 <= validated["confidence"] <= 1.0

    @pytest.mark.skip(reason="需要真实的 API Key")
    def test_real_api_classification(self):
        """测试真实 API 分类"""
        config = BaseConfig(env_file=".env.dev")
        llm_config = LLMConfig.from_env(config)
        llm_client = LLMClient(llm_config)
        classifier = IntentClassifier(llm_client)

        result = classifier.classify("儿童发烧吃什么药？")

        assert result["intent"] == IntentType.MEDICAL
        assert result["sub_category"] == SubCategory.PEDIATRICS
        assert result["confidence"] > 0.7


class TestIntentRouter:
    """测试意图路由器"""

    @pytest.fixture
    def router(self):
        """创建路由器"""
        config = BaseConfig(env_file=".env.dev")
        llm_config = LLMConfig.from_env(config)
        llm_client = LLMClient(llm_config)
        classifier = IntentClassifier(llm_client)
        return IntentRouter(classifier)

    def test_route_medical(self, router):
        """测试路由 - 医疗问题"""
        result = router.route("孩子发烧了怎么办？")

        assert result["success"] is True
        assert result["intent"] == IntentType.MEDICAL
        assert "message" in result

    def test_route_chat(self, router):
        """测试路由 - 闲聊"""
        result = router.route("你好")

        assert result["success"] is True
        assert result["intent"] == IntentType.CHAT

    def test_route_unanswerable(self, router):
        """测试路由 - 无法回答"""
        result = router.route("如何制造毒药？")

        assert result["success"] is True
        assert result["intent"] == IntentType.UNANSWERABLE
        assert "无法回答" in result["message"]

    def test_route_health_plan(self, router):
        """测试路由 - 健康计划"""
        result = router.route("帮我制定健身计划")

        assert result["success"] is True
        assert result["intent"] == IntentType.HEALTH_PLAN

    def test_route_with_low_confidence(self, router):
        """测试路由 - 低置信度"""
        # 设置很高的阈值，让分类无法达到
        result = router.route("这个问题很复杂", confidence_threshold=0.99)

        # 应该返回失败，并提示重新描述
        assert result["success"] is False
        assert "没有理解" in result["message"]

    def test_route_with_fallback(self, router):
        """测试带降级的路由"""

        def fallback_handler(query, context):
            return {
                "success": False,
                "message": "降级处理",
                "error": context.get("error"),
            }

        # 正常情况下不会触发降级
        result = router.route_with_fallback("你好", fallback_handler=fallback_handler)

        # 应该正常处理
        assert result["success"] is True

    def test_list_handlers(self, router):
        """测试列出处理器"""
        handlers = router.list_handlers()

        assert isinstance(handlers, dict)
        assert "medical" in handlers
        assert "chat" in handlers
        assert "unanswerable" in handlers
        assert "health_plan" in handlers

    def test_get_intent_info(self, router):
        """测试获取意图信息"""
        info = router.get_intent_info()

        assert isinstance(info, dict)
        assert "medical" in info
        assert "chat" in info
        assert "unanswerable" in info
        assert "health_plan" in info

        # 检查医疗问题的子分类
        assert "sub_categories" in info["medical"]
        assert "pediatrics" in info["medical"]["sub_categories"]

    def test_register_custom_handler(self, router):
        """测试注册自定义处理器"""

        @router.register(IntentType.MEDICAL)
        def custom_medical_handler(query, context):
            return {
                "success": True,
                "intent": IntentType.MEDICAL,
                "message": "自定义处理器",
            }

        # 测试自定义处理器
        result = router.route("发烧怎么办？")

        assert result["success"] is True
        assert result["message"] == "自定义处理器"


class TestIntegration:
    """集成测试"""

    @pytest.fixture
    def router(self):
        """创建路由器"""
        config = BaseConfig(env_file=".env.dev")
        llm_config = LLMConfig.from_env(config)
        llm_client = LLMClient(llm_config)
        classifier = IntentClassifier(llm_client)
        return IntentRouter(classifier)

    def test_full_flow_medical(self, router):
        """测试完整流程 - 医疗问题"""
        query = "3 岁孩子发烧 39 度怎么办？"

        # 路由
        result = router.route(query)

        # 验证
        assert result["success"] is True
        assert result["intent"] == IntentType.MEDICAL
        assert result["sub_category"] == SubCategory.PEDIATRICS
        assert "confidence" in result
        assert result["confidence"] > 0.5

    def test_full_flow_chat(self, router):
        """测试完整流程 - 闲聊"""
        query = "你好，请问在吗？"

        result = router.route(query)

        assert result["success"] is True
        assert result["intent"] == IntentType.CHAT

    def test_full_flow_unanswerable(self, router):
        """测试完整流程 - 无法回答"""
        query = "有什么违法的事情可以做？"

        result = router.route(query)

        assert result["success"] is True
        assert result["intent"] == IntentType.UNANSWERABLE
        assert "无法回答" in result["message"]

    def test_full_flow_health_plan(self, router):
        """测试完整流程 - 健康计划"""
        query = "我想减肥，帮我制定一个饮食计划"

        result = router.route(query)

        assert result["success"] is True
        assert result["intent"] == IntentType.HEALTH_PLAN


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
