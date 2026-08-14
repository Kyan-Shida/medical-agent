"""
意图路由器模块
根据意图分类结果路由到不同的处理分支
"""

from typing import Dict, Any, Optional, Callable
from utils.log_utils import get_logger
from utils.exception_utils import IntentClassificationError
from core.intent.classifier import IntentClassifier, IntentType, SubCategory
from core.intent.handlers import (
    MedicalHandler,
    ChatHandler,
    UnanswerableHandler,
    HealthPlanHandler,
)

logger = get_logger(__name__)


class IntentRouter:
    """意图路由器"""

    def __init__(
        self,
        classifier: IntentClassifier,
        llm_client=None,
        retriever=None,
    ):
        """
        初始化意图路由器

        Args:
            classifier: 意图分类器
            llm_client: LLM 客户端（可选，用于业务处理）
            retriever: RAG 检索器（可选）
        """
        self.classifier = classifier
        self.llm_client = llm_client
        self.retriever = retriever
        self.logger = get_logger(__name__)

        # 注册处理器
        self.handlers: Dict[IntentType, Callable] = {}

        # 注册业务处理器
        self._register_business_handlers()

    def register(self, intent_type: IntentType):
        """
        注册处理器装饰器

        Args:
            intent_type: 意图类型

        Returns:
            装饰器

        Example:
            @router.register(IntentType.MEDICAL)
            def handle_medical(query: str, context: dict) -> dict:
                ...
        """

        def decorator(func: Callable) -> Callable:
            self.handlers[intent_type] = func
            self.logger.debug(f"注册处理器：{intent_type.value} -> {func.__name__}")
            return func

        return decorator


    def _register_business_handlers(self):
        """注册业务处理器"""
        # 创建业务处理器实例
        medical_handler = MedicalHandler(self.llm_client, self.retriever)
        chat_handler = ChatHandler(self.llm_client)
        unanswerable_handler = UnanswerableHandler(self.llm_client)
        health_plan_handler = HealthPlanHandler(self.llm_client)

        # 注册处理器
        @self.register(IntentType.MEDICAL)
        def handle_medical(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
            """处理医疗问题"""
            self.logger.info(f"路由到医疗问题处理器：{query[:50]}...")
            return medical_handler.handle(query, context)

        @self.register(IntentType.CHAT)
        def handle_chat(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
            """处理闲聊"""
            self.logger.info(f"路由到闲聊处理器：{query[:50]}...")
            return chat_handler.handle(query, context)

        @self.register(IntentType.UNANSWERABLE)
        def handle_unanswerable(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
            """处理无法回答的问题"""
            self.logger.info(f"路由到无法回答处理器：{query[:50]}...")
            return unanswerable_handler.handle(query, context)

        @self.register(IntentType.HEALTH_PLAN)
        def handle_health_plan(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
            """处理健康计划"""
            self.logger.info(f"路由到健康计划处理器：{query[:50]}...")
            return health_plan_handler.handle(query, context)

    # 路由用户查询（对外接口）
    def route(
        self,
        query: str,
        confidence_threshold: float = 0.7,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        路由用户查询（对外接口）

        Args:
            query: 用户输入
            confidence_threshold: 置信度阈值
            **kwargs: 其他参数

        Returns:
            处理结果

        Raises:
            IntentClassificationError: 分类失败
        """
        try:
            self.logger.info(f"开始路由：{query[:50]}...")

            # 1. 意图分类
            classification = self.classifier.classify(query)

            intent = classification["intent"]
            confidence = classification["confidence"]
            sub_category = classification.get("sub_category")
            reason = classification.get("reason", "")

            self.logger.info(
                f"分类结果：{intent.value} "
                f"(置信度：{confidence:.2f}, 理由：{reason})"
            )

            # 2. 检查置信度
            if confidence < confidence_threshold:
                self.logger.warning(
                    f"置信度过低：{confidence:.2f} < {confidence_threshold}"
                )
                # 低置信度时使用默认回复
                return {
                    "success": False,
                    "intent": intent,
                    "confidence": confidence,
                    "message": "抱歉，我没有理解您的问题，请您换一种方式描述。",
                    "query": query,
                }

            # 3. 获取处理器
            handler = self.handlers.get(intent)

            if not handler:
                self.logger.error(f"未找到处理器：{intent.value}")
                return {
                    "success": False,
                    "intent": intent,
                    "message": f"暂不支持该类型问题：{intent.value}",
                    "query": query,
                }

            # 4. 执行处理器
            context = {
                "classification": classification,
                "sub_category": sub_category,
                "reason": reason,
                **kwargs,
            }

            result = handler(query, context)
            result["confidence"] = confidence
            result["classification_reason"] = reason

            self.logger.info(f"路由完成：{intent.value} -> {result.get('success', False)}")

            return result

        except IntentClassificationError:
            raise
        except Exception as e:
            self.logger.error(f"路由失败：{e}")
            raise IntentClassificationError(
                message=f"路由失败：{str(e)}",
                code="ROUTING_FAILED",
                details={"query": query[:100]},
            )

    def route_with_fallback(
        self,
        query: str,
        fallback_handler: Optional[Callable] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        带降级的路由

        Args:
            query: 用户输入
            fallback_handler: 降级处理器
            **kwargs: 其他参数

        Returns:
            处理结果
        """
        try:
            return self.route(query, **kwargs)
        except Exception as e:
            self.logger.error(f"路由失败，使用降级：{e}")

            if fallback_handler:
                return fallback_handler(query, {"error": str(e)})
            else:
                return {
                    "success": False,
                    "intent": None,
                    "message": "抱歉，系统出现错误，请稍后重试。",
                    "query": query,
                    "error": str(e),
                }

    def get_handler(self, intent_type: IntentType) -> Optional[Callable]:
        """
        获取处理器

        Args:
            intent_type: 意图类型

        Returns:
            处理器函数
        """
        return self.handlers.get(intent_type)

    def list_handlers(self) -> Dict[str, str]:
        """
        列出所有注册的处理器

        Returns:
            处理器字典
        """
        return {
            intent.value: handler.__name__ for intent, handler in self.handlers.items()
        }

    def get_intent_info(self) -> Dict[str, Dict[str, Any]]:
        """
        获取意图类型信息

        Returns:
            意图信息字典
        """
        return {
            IntentType.MEDICAL.value: {
                "name": "医疗问题",
                "description": "症状咨询、疾病诊断、用药建议、治疗方案等",
                "sub_categories": [
                    SubCategory.PEDIATRICS.value,
                    SubCategory.GENERAL.value,
                ],
            },
            IntentType.CHAT.value: {
                "name": "闲聊",
                "description": "问候、日常对话、感谢等",
                "sub_categories": [],
            },
            IntentType.UNANSWERABLE.value: {
                "name": "无法回答",
                "description": "涉及政治、色情、暴力、违法等敏感话题",
                "sub_categories": [],
            },
            IntentType.HEALTH_PLAN.value: {
                "name": "每日健康计划",
                "description": "制定健康计划、饮食计划、运动计划等",
                "sub_categories": [],
            },
        }
