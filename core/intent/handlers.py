"""
业务处理器模块
实现不同意图类型的具体处理逻辑
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from utils.log_utils import get_logger
from core.llm.client import LLMClient
from core.rag.retriever import Retriever
from core.intent.classifier import IntentType, SubCategory

logger = get_logger(__name__)


class MedicalHandler:
    """医疗问题处理器"""

    def __init__(self, llm_client: LLMClient, retriever: Optional[Retriever] = None):
        """
        初始化医疗问题处理器

        Args:
            llm_client: LLM 客户端
            retriever: RAG 检索器（可选）
        """
        self.llm_client = llm_client
        self.retriever = retriever
        self.logger = get_logger(__name__)

    def handle(
        self, query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理医疗问题

        Args:
            query: 用户问题
            context: 上下文信息

        Returns:
            处理结果
        """
        try:
            self.logger.info(f"处理医疗问题：{query[:50]}...")

            sub_category = context.get("sub_category")
            classification_reason = context.get("reason", "")

            # 1. RAG 检索（如果有检索器）
            rag_context = ""
            retrieved_docs: List[Dict[str, Any]] = []

            if self.retriever:
                try:
                    results = self.retriever.retrieve(query)
                    retrieved_docs = [
                        {"content": doc.content, "score": score}
                        for doc, score in results
                    ]
                    rag_context = self.retriever.retrieve_with_context(query)
                    self.logger.info(
                        f"RAG 检索到 {len(results)} 个相关文档"
                    )
                except Exception as e:
                    self.logger.warning(f"RAG 检索失败：{e}，使用纯 LLM 回答")

            # 2. 构建提示
            if rag_context:
                system_prompt = self._build_medical_system_prompt(sub_category)
                prompt = self._build_medical_prompt_with_rag(
                    query, rag_context, sub_category
                )
            else:
                system_prompt = self._build_medical_system_prompt(sub_category)
                prompt = self._build_medical_prompt(query, sub_category)

            # 调用 LLM
            self.logger.info("调用 LLM 生成医疗回答")
            response = self.llm_client.simple_chat(
                prompt=prompt,
                system_prompt=system_prompt,
            )

            # 4. 构建响应
            result = {
                "success": True,
                "intent": IntentType.MEDICAL,
                "sub_category": sub_category,
                "query": query,
                "response": response,
                "has_rag_context": bool(rag_context),
                "retrieved_docs": retrieved_docs,
                "classification_reason": classification_reason,
                "metadata": {
                    "response_length": len(response),
                    "timestamp": datetime.now().isoformat(),
                },
            }

            self.logger.info(f"医疗问题处理完成，回答长度：{len(response)}")
            return result

        except Exception as e:
            self.logger.error(f"医疗问题处理失败：{e}")
            return {
                "success": False,
                "intent": IntentType.MEDICAL,
                "message": "抱歉，处理医疗问题时出现错误，请稍后重试。",
                "error": str(e),
                "query": query,
            }

    def _build_medical_system_prompt(
        self, sub_category: Optional[SubCategory]
    ) -> str:
        """构建医疗系统提示"""
        base_prompt = """你是一个专业、负责、易懂的医疗助手。
你的职责是回答用户的医疗健康问题，提供准确、科学、实用的建议。

回答原则：
1. 专业准确：基于医学知识和临床指南
2. 通俗易懂：避免过多专业术语，必要时解释
3. 谨慎负责：不替代医生诊断，建议及时就医
4. 结构清晰：分点回答，重点突出
5. 温暖关怀：体现对患者的关心和理解"""

        if sub_category == SubCategory.PEDIATRICS:
            base_prompt += """

特别注意（儿科）：
- 儿童不是成人的缩小版，需要特别的医疗关注
- 用药剂量需要根据年龄、体重调整
- 儿童病情变化快，需要密切观察
- 安抚家长情绪，提供清晰的护理指导"""

        return base_prompt

    def _build_medical_prompt_with_rag(
        self, query: str, context: str, sub_category: Optional[SubCategory]
    ) -> str:
        """构建带 RAG 上下文的医疗提示"""
        return f"""请根据以下医疗知识回答问题：

【参考知识】
{context}

【患者问题】
{query}

请结合上述知识，提供专业、准确、易懂的医疗建议。
如果知识库内容与问题不完全匹配，也请基于你的医学知识给出建议。"""

    def _build_medical_prompt(
        self, query: str, sub_category: Optional[SubCategory]
    ) -> str:
        """构建纯 LLM 医疗提示"""
        return f"""请回答以下医疗问题：

【患者问题】
{query}

请提供专业、准确、易懂的医疗建议。
包括：
1. 可能的原因分析
2. 建议的处理方法
3. 何时需要就医
4. 日常护理注意事项"""


class ChatHandler:
    """闲聊处理器"""

    def __init__(self, llm_client: LLMClient):
        """
        初始化闲聊处理器

        Args:
            llm_client: LLM 客户端
        """
        self.llm_client = llm_client
        self.logger = get_logger(__name__)

    def handle(
        self, query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理闲聊

        Args:
            query: 用户输入
            context: 上下文信息

        Returns:
            处理结果
        """
        try:
            self.logger.info(f"处理闲聊：{query[:50]}...")

            # 构建提示
            system_prompt = """你是一个友好、幽默、温暖的聊天助手。
你的职责是与用户进行轻松愉快的对话。

回答原则：
1. 友好亲切：像朋友一样交流
2. 幽默风趣：适当使用幽默
3. 简洁自然：避免过于正式
4. 积极正面：传递正能量"""

            prompt = f"""用户说：{query}

请用自然、友好的方式回复用户。"""

            # 调用 LLM
            response = self.llm_client.simple_chat(
                prompt=prompt,
                system_prompt=system_prompt,
            )

            # 构建响应
            result = {
                "success": True,
                "intent": IntentType.CHAT,
                "query": query,
                "response": response,
                "metadata": {
                    "response_length": len(response),
                    "timestamp": datetime.now().isoformat(),
                },
            }

            self.logger.info(f"闲聊处理完成，回答长度：{len(response)}")
            return result

        except Exception as e:
            self.logger.error(f"闲聊处理失败：{e}")
            return {
                "success": False,
                "intent": IntentType.CHAT,
                "message": "抱歉，我好像走神了，能再说一次吗？",
                "error": str(e),
                "query": query,
            }


class UnanswerableHandler:
    """无法回答的问题处理器"""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        初始化无法回答的处理器

        Args:
            llm_client: LLM 客户端（可选，用于生成委婉回复）
        """
        self.llm_client = llm_client
        self.logger = get_logger(__name__)

    def handle(
        self, query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理无法回答的问题

        Args:
            query: 用户输入
            context: 上下文信息

        Returns:
            处理结果
        """
        try:
            self.logger.info(f"处理无法回答的问题：{query[:50]}...")

            classification_reason = context.get("reason", "")

            # 标准回复
            standard_response = """抱歉，这个问题我暂时无法回答。

我是一个专注于医疗健康领域的助手，主要为您提供：
- 症状咨询
- 疾病科普
- 用药指导
- 健康建议
- 日常护理

如果您有医疗健康相关的问题，我很乐意为您解答！"""

            # 如果有 LLM，可以生成更自然的回复
            if self.llm_client:
                try:
                    system_prompt = """你是一个医疗助手，遇到无法回答的问题时，
要礼貌、委婉地说明，并引导用户提出医疗健康相关的问题。"""

                    prompt = f"""用户问了一个你无法回答的问题：{query}

请礼貌地说明你无法回答，并引导用户提出医疗健康相关的问题。"""

                    response = self.llm_client.simple_chat(
                        prompt=prompt,
                        system_prompt=system_prompt,
                    )
                except Exception as e:
                    self.logger.warning(f"LLM 生成失败，使用标准回复：{e}")
                    response = standard_response
            else:
                response = standard_response

            # 构建响应
            result = {
                "success": True,
                "intent": IntentType.UNANSWERABLE,
                "query": query,
                "response": response,
                "classification_reason": classification_reason,
                "metadata": {
                    "response_length": len(response),
                    "timestamp": datetime.now().isoformat(),
                },
            }

            self.logger.info(f"无法回答问题处理完成")
            return result

        except Exception as e:
            self.logger.error(f"无法回答问题处理失败：{e}")
            return {
                "success": False,
                "intent": IntentType.UNANSWERABLE,
                "message": "抱歉，这个问题我暂时无法回答。",
                "error": str(e),
                "query": query,
            }


class HealthPlanHandler:
    """健康计划处理器"""

    def __init__(self, llm_client: LLMClient):
        """
        初始化健康计划处理器

        Args:
            llm_client: LLM 客户端
        """
        self.llm_client = llm_client
        self.logger = get_logger(__name__)

    def handle(
        self, query: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理健康计划

        Args:
            query: 用户输入
            context: 上下文信息

        Returns:
            处理结果
        """
        try:
            self.logger.info(f"处理健康计划：{query[:50]}...")

            # 构建提示
            system_prompt = """你是一个专业的健康规划师。
你的职责是根据用户的需求，制定科学、可行、个性化的健康计划。

计划原则：
1. 科学合理：基于营养学、运动医学等科学知识
2. 个性化：考虑用户的年龄、性别、身体状况等
3. 可行实用：容易执行，融入日常生活
4. 循序渐进：分阶段、分步骤
5. 安全第一：避免过度节食、过度运动等不健康方式"""

            prompt = f"""请为用户制定健康计划：

【用户需求】
{query}

请提供：
1. 目标设定（具体、可衡量、可实现）
2. 饮食计划（三餐建议、营养搭配）
3. 运动计划（运动类型、频率、强度）
4. 作息建议（睡眠、休息）
5. 注意事项（安全提示、常见误区）
6. 执行建议（如何坚持、如何调整）"""

            # 调用 LLM
            response = self.llm_client.simple_chat(
                prompt=prompt,
                system_prompt=system_prompt,
            )

            # 构建响应
            result = {
                "success": True,
                "intent": IntentType.HEALTH_PLAN,
                "query": query,
                "response": response,
                "metadata": {
                    "response_length": len(response),
                    "timestamp": datetime.now().isoformat(),
                },
            }

            self.logger.info(f"健康计划处理完成，回答长度：{len(response)}")
            return result

        except Exception as e:
            self.logger.error(f"健康计划处理失败：{e}")
            return {
                "success": False,
                "intent": IntentType.HEALTH_PLAN,
                "message": "抱歉，制定健康计划时出现错误，请稍后重试。",
                "error": str(e),
                "query": query,
            }


def create_handlers(
    llm_client: LLMClient,
    retriever: Optional[Retriever] = None,
) -> Dict[str, Any]:
    """
    创建所有处理器

    Args:
        llm_client: LLM 客户端
        retriever: RAG 检索器（可选）

    Returns:
        处理器字典
    """
    return {
        IntentType.MEDICAL: MedicalHandler(llm_client, retriever),
        IntentType.CHAT: ChatHandler(llm_client),
        IntentType.UNANSWERABLE: UnanswerableHandler(llm_client),
        IntentType.HEALTH_PLAN: HealthPlanHandler(llm_client),
    }
