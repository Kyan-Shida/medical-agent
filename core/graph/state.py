"""
LangGraph 状态模式定义
定义 Agent 工作流中流转的状态数据结构
"""
from typing import TypedDict, List, Dict, Any, Optional, Literal
from datetime import datetime


class AgentState(TypedDict, total=False):
    """
    Agent 状态定义
    
    这是 LangGraph 工作流中流转的完整状态，包含：
    - 用户输入和对话历史
    - 意图识别结果（由监督者节点产生）
    - RAG 检索结果
    - 各节点处理结果
    - 错误信息
    """
    
    # ========== 输入相关 ==========
    query: str  # 当前用户输入
    session_id: str  # 会话ID
    conversation_history: List[Dict[str, str]]  # 对话历史 [{role, content}]
    
    # ========== 监督者决策 ==========
    intent: str  # 意图类型: medical/chat/unanswerable/health_plan
    confidence: float  # 置信度 0.0-1.0
    sub_category: Optional[str]  # 子分类: pediatrics/general (仅医疗问题)
    reason: str  # 分类理由
    next_node: str  # 下一个执行的节点名称（监督者决策结果）
    
    # ========== RAG 相关 ==========
    retrieved_docs: List[Dict[str, Any]]  # 检索到的文档列表
    rag_context: str  # 拼接的 RAG 上下文
    has_rag_context: bool  # 是否有 RAG 上下文
    
    # ========== 输出相关 ==========
    response: str  # AI 最终回复
    response_metadata: Dict[str, Any]  # 回复元数据
    
    # ========== 追踪信息 ==========
    execution_path: List[str]  # 执行路径（经过的节点列表）
    timestamp: str  # 时间戳
    error: Optional[str]  # 错误信息


class NodeName:
    """
    节点名称常量
    
    监督者返回的节点名称必须与此处定义一致，
    这是 LangGraph 条件路由的关键约束
    """
    
    # 核心节点
    SUPERVISOR = "supervisor"  # 监督者（LLM 路由决策）
    MEDICAL_HANDLER = "medical_handler"  # 医疗问题处理
    CHAT_HANDLER = "chat_handler"  # 闲聊处理
    UNANSWERABLE_HANDLER = "unanswerable_handler"  # 无法回答处理
    HEALTH_PLAN_HANDLER = "health_plan_handler"  # 健康计划处理
    END = "end"  # 结束节点
    
    # 所有业务处理节点
    BUSINESS_NODES = [
        MEDICAL_HANDLER,
        CHAT_HANDLER,
        UNANSWERABLE_HANDLER,
        HEALTH_PLAN_HANDLER,
    ]


# 意图类型映射（与 NodeName 对应）
INTENT_TO_NODE_MAP: Dict[str, str] = {
    "medical": NodeName.MEDICAL_HANDLER,
    "chat": NodeName.CHAT_HANDLER,
    "unanswerable": NodeName.UNANSWERABLE_HANDLER,
    "health_plan": NodeName.HEALTH_PLAN_HANDLER,
}


# 节点描述（用于监督者 Prompt）
NODE_DESCRIPTIONS: Dict[str, str] = {
    NodeName.MEDICAL_HANDLER: "处理医疗问题：症状咨询、疾病诊断、用药建议、治疗方案等",
    NodeName.CHAT_HANDLER: "处理闲聊：问候、日常对话、感谢、打招呼等",
    NodeName.UNANSWERABLE_HANDLER: "处理无法回答的问题：涉及政治、色情、暴力、违法等敏感话题",
    NodeName.HEALTH_PLAN_HANDLER: "处理健康计划：制定减肥计划、饮食计划、运动计划、作息计划等",
}


def create_initial_state(
    query: str,
    session_id: str = "",
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> AgentState:
    """
    创建初始状态
    
    Args:
        query: 用户输入
        session_id: 会话ID
        conversation_history: 对话历史
    
    Returns:
        初始 AgentState
    """
    return AgentState(
        query=query,
        session_id=session_id or f"session_{datetime.now().timestamp():.0f}",
        conversation_history=conversation_history or [],
        intent="",
        confidence=0.0,
        sub_category=None,
        reason="",
        next_node="",
        retrieved_docs=[],
        rag_context="",
        has_rag_context=False,
        response="",
        response_metadata={},
        execution_path=["start"],
        timestamp=datetime.now().isoformat(),
        error=None,
    )
