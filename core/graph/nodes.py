"""
业务节点封装
将现有 Handler 封装为 LangGraph 可调用的节点函数

设计原则：
- 不修改现有 Handler 代码
- 每个节点函数接收 AgentState，返回更新后的 AgentState
- 节点函数内调用现有 Handler 完成业务逻辑
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from core.graph.state import AgentState, NodeName
from core.intent.handlers import (
    MedicalHandler,
    ChatHandler,
    UnanswerableHandler,
    HealthPlanHandler,
)
from utils.log_utils import get_logger

logger = get_logger(__name__)


class BusinessNodes:
    """
    业务节点集合
    
    封装四种业务处理逻辑为 LangGraph 节点
    """
    
    def __init__(self, llm_client, retriever=None):
        """
        初始化业务节点
        
        Args:
            llm_client: LLM 客户端实例
            retriever: RAG 检索器实例（可选）
        """
        self.llm_client = llm_client
        self.retriever = retriever
        
        # 初始化现有处理器
        self.medical_handler = MedicalHandler(llm_client, retriever)
        self.chat_handler = ChatHandler(llm_client)
        self.unanswerable_handler = UnanswerableHandler(llm_client)
        self.health_plan_handler = HealthPlanHandler(llm_client)
        
        self.logger = get_logger(__name__)
    
    def medical_node(self, state: AgentState) -> AgentState:
        """
        医疗问题处理节点
        
        流程：
        1. 获取 RAG 检索结果
        2. 调用 MedicalHandler 处理
        3. 更新状态
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            更新后的状态
        """
        query = state.get("query", "")
        sub_category = state.get("sub_category")
        reason = state.get("reason", "")
        
        self.logger.info(f"[医疗节点] 处理医疗问题：{query[:50]}...")
        
        try:
            # 构建上下文
            context = {
                "classification": {
                    "intent": "medical",
                    "confidence": state.get("confidence", 0.0),
                    "reason": reason,
                },
                "sub_category": sub_category,
                "reason": reason,
            }
            
            # 调用现有处理器
            result = self.medical_handler.handle(query, context)
            
            # 更新状态
            state["response"] = result.get("response", "")
            state["has_rag_context"] = result.get("has_rag_context", False)
            state["retrieved_docs"] = result.get("retrieved_docs", [])
            state["response_metadata"] = result.get("metadata", {})
            state["execution_path"] = state.get("execution_path", []) + [NodeName.MEDICAL_HANDLER]
            
            # 更新 RAG 上下文到状态
            if self.retriever:
                try:
                    rag_context = self.retriever.retrieve_with_context(query)
                    state["rag_context"] = rag_context
                    state["has_rag_context"] = bool(rag_context)
                except Exception as e:
                    self.logger.warning(f"RAG 检索失败：{e}")
            
            self.logger.info(
                f"[医疗节点] 处理完成，回答长度：{len(state['response'])}"
            )
            
        except Exception as e:
            self.logger.error(f"[医疗节点] 处理失败：{e}")
            state["response"] = "抱歉，处理医疗问题时出现错误，请稍后重试。"
            state["error"] = str(e)
            state["execution_path"] = state.get("execution_path", []) + [NodeName.MEDICAL_HANDLER]
        
        return state
    
    def chat_node(self, state: AgentState) -> AgentState:
        """
        闲聊处理节点
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            更新后的状态
        """
        query = state.get("query", "")
        
        self.logger.info(f"[闲聊节点] 处理闲聊：{query[:50]}...")
        
        try:
            context = {"reason": state.get("reason", "")}
            result = self.chat_handler.handle(query, context)
            
            state["response"] = result.get("response", "")
            state["response_metadata"] = result.get("metadata", {})
            state["execution_path"] = state.get("execution_path", []) + [NodeName.CHAT_HANDLER]
            
            self.logger.info(
                f"[闲聊节点] 处理完成，回答长度：{len(state['response'])}"
            )
            
        except Exception as e:
            self.logger.error(f"[闲聊节点] 处理失败：{e}")
            state["response"] = "抱歉，我好像走神了，能再说一次吗？"
            state["error"] = str(e)
            state["execution_path"] = state.get("execution_path", []) + [NodeName.CHAT_HANDLER]
        
        return state
    
    def unanswerable_node(self, state: AgentState) -> AgentState:
        """
        无法回答处理节点
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            更新后的状态
        """
        query = state.get("query", "")
        reason = state.get("reason", "")
        
        self.logger.info(f"[无法回答节点] 处理问题：{query[:50]}...")
        
        try:
            context = {"reason": reason}
            result = self.unanswerable_handler.handle(query, context)
            
            state["response"] = result.get("response", "")
            state["response_metadata"] = result.get("metadata", {})
            state["execution_path"] = state.get("execution_path", []) + [NodeName.UNANSWERABLE_HANDLER]
            
            self.logger.info("[无法回答节点] 处理完成")
            
        except Exception as e:
            self.logger.error(f"[无法回答节点] 处理失败：{e}")
            state["response"] = "抱歉，这个问题我暂时无法回答。"
            state["error"] = str(e)
            state["execution_path"] = state.get("execution_path", []) + [NodeName.UNANSWERABLE_HANDLER]
        
        return state
    
    def health_plan_node(self, state: AgentState) -> AgentState:
        """
        健康计划处理节点
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            更新后的状态
        """
        query = state.get("query", "")
        
        self.logger.info(f"[健康计划节点] 处理健康计划：{query[:50]}...")
        
        try:
            context = {}
            result = self.health_plan_handler.handle(query, context)
            
            state["response"] = result.get("response", "")
            state["response_metadata"] = result.get("metadata", {})
            state["execution_path"] = state.get("execution_path", []) + [NodeName.HEALTH_PLAN_HANDLER]
            
            self.logger.info(
                f"[健康计划节点] 处理完成，回答长度：{len(state['response'])}"
            )
            
        except Exception as e:
            self.logger.error(f"[健康计划节点] 处理失败：{e}")
            state["response"] = "抱歉，制定健康计划时出现错误，请稍后重试。"
            state["error"] = str(e)
            state["execution_path"] = state.get("execution_path", []) + [NodeName.HEALTH_PLAN_HANDLER]
        
        return state


# ==================== 节点函数（供 LangGraph 直接引用）====================
# 使用闭包模式，将 BusinessNodes 实例方法包装为独立函数

def create_node_functions(
    llm_client,
    retriever=None,
) -> Dict[str, Any]:
    """
    创建节点函数映射
    
    Args:
        llm_client: LLM 客户端
        retriever: RAG 检索器（可选）
    
    Returns:
        节点名称 -> 节点函数 的映射字典
    """
    business = BusinessNodes(llm_client, retriever)
    
    return {
        NodeName.MEDICAL_HANDLER: business.medical_node,
        NodeName.CHAT_HANDLER: business.chat_node,
        NodeName.UNANSWERABLE_HANDLER: business.unanswerable_node,
        NodeName.HEALTH_PLAN_HANDLER: business.health_plan_node,
    }
