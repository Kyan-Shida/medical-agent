"""
LangGraph 工作流构建器
构建基于监督者模式的医疗 Agent 工作流

架构说明：
- START → supervisor（监督者 LLM 决策）→ 条件路由 → 业务节点 → END
- 监督者由 LLM 驱动，动态决定路由到哪个处理器
- 业务节点封装现有 Handler，实现零侵入升级

工作流图：
    ┌─────────┐
    │  START   │
    └────┬─────┘
         │
    ┌────▼─────┐
    │SUPERVISOR │  ← LLM 动态决策
    └────┬─────┘
         │
    ┌────▼─────┐
    │条件路由   │  ← 根据 next_node 分发
    └────┬─────┘
         │
    ┌────▼─────┐
    │ 业务节点  │  ← medical/chat/unanswerable/health_plan
    └────┬─────┘
         │
    ┌────▼─────┐
    │   END    │
    └──────────┘
"""
from typing import Dict, Any, Optional, Callable
from langgraph.graph import StateGraph, END
from core.graph.state import AgentState, NodeName
from core.graph.llm_adapter import LLMAdapter
from core.graph.supervisor import Supervisor
from core.graph.nodes import create_node_functions
from utils.log_utils import get_logger

logger = get_logger(__name__)


def build_medical_agent_graph(
    llm_client,
    retriever=None,
) -> StateGraph:
    """
    构建医疗 Agent 工作流图
    
    核心设计：
    1. 监督者节点：LLM 动态决策路由
    2. 条件边：根据监督者的 next_node 分发到不同处理器
    3. 业务节点：封装现有 Handler 完成业务逻辑
    
    Args:
        llm_client: 现有 LLMClient 实例
        retriever: RAG 检索器实例（可选）
    
    Returns:
        编译后的 StateGraph
    """
    logger.info("=" * 60)
    logger.info("🔧 构建医疗 Agent LangGraph 工作流")
    logger.info("=" * 60)
    
    # 1. 创建 LLM 适配器
    llm_adapter = LLMAdapter(llm_client)
    logger.info("✅ LLM 适配器创建完成")
    
    # 2. 创建监督者
    supervisor = Supervisor(llm_adapter)
    logger.info("✅ 监督者创建完成")
    
    # 3. 创建业务节点函数
    node_functions = create_node_functions(llm_client, retriever)
    logger.info(f"✅ 业务节点创建完成：{list(node_functions.keys())}")
    
    # 4. 定义条件路由函数
    def route_by_supervisor(state: AgentState) -> str:
        """
        条件路由函数：根据监督者决策选择下一个节点
        
        关键约束：
        返回值必须与 add_node 注册的节点名完全一致！
        这是 LangGraph 条件路由的核心机制。
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            下一个节点名称
        """
        next_node = state.get("next_node", NodeName.CHAT_HANDLER)
        
        # 验证节点名称有效性
        valid_nodes = [
            NodeName.MEDICAL_HANDLER,
            NodeName.CHAT_HANDLER,
            NodeName.UNANSWERABLE_HANDLER,
            NodeName.HEALTH_PLAN_HANDLER,
        ]
        
        if next_node not in valid_nodes:
            logger.warning(f"[路由] 无效的节点：{next_node}，路由到闲聊")
            return NodeName.CHAT_HANDLER
        
        logger.info(f"[路由] 监督者决策：{next_node}")
        return next_node
    
    # 5. 构建图
    workflow = StateGraph(AgentState)
    logger.info("✅ StateGraph 创建完成")
    
    # 添加监督者节点
    workflow.add_node(
        NodeName.SUPERVISOR,
        lambda state: supervisor.run(state),
    )
    logger.info(f"✅ 添加节点：{NodeName.SUPERVISOR}")
    
    # 添加业务节点
    for node_name, node_func in node_functions.items():
        workflow.add_node(node_name, node_func)
        logger.info(f"✅ 添加节点：{node_name}")
    
    # 设置入口
    workflow.set_entry_point(NodeName.SUPERVISOR)
    logger.info(f"✅ 设置入口：START → {NodeName.SUPERVISOR}")
    
    # 设置条件边：监督者 → 路由决策
    workflow.add_conditional_edges(
        NodeName.SUPERVISOR,
        route_by_supervisor,
        {
            NodeName.MEDICAL_HANDLER: NodeName.MEDICAL_HANDLER,
            NodeName.CHAT_HANDLER: NodeName.CHAT_HANDLER,
            NodeName.UNANSWERABLE_HANDLER: NodeName.UNANSWERABLE_HANDLER,
            NodeName.HEALTH_PLAN_HANDLER: NodeName.HEALTH_PLAN_HANDLER,
        },
    )
    logger.info("✅ 添加条件边：SUPERVISOR → 路由决策")
    
    # 设置业务节点 → END
    for node_name in [
        NodeName.MEDICAL_HANDLER,
        NodeName.CHAT_HANDLER,
        NodeName.UNANSWERABLE_HANDLER,
        NodeName.HEALTH_PLAN_HANDLER,
    ]:
        workflow.add_edge(node_name, END)
        logger.info(f"✅ 添加边：{node_name} → END")
    
    # 编译图
    graph = workflow.compile()
    logger.info("✅ 工作流编译完成")
    logger.info("=" * 60)
    logger.info("🎯 工作流构建成功！")
    logger.info("=" * 60)
    
    return graph


def run_graph(
    graph: StateGraph,
    query: str,
    session_id: str = "",
    conversation_history: Optional[list] = None,
) -> Dict[str, Any]:
    """
    运行工作流
    
    Args:
        graph: 编译后的 StateGraph
        query: 用户输入
        session_id: 会话ID
        conversation_history: 对话历史
    
    Returns:
        工作流执行结果
    """
    from core.graph.state import create_initial_state
    
    # 创建初始状态
    initial_state = create_initial_state(
        query=query,
        session_id=session_id,
        conversation_history=conversation_history,
    )
    
    logger.info(f"[执行] 开始处理：{query[:50]}...")
    
    # 运行图
    try:
        result = graph.invoke(initial_state)
        logger.info(f"[执行] 处理完成")
        return result
    except Exception as e:
        logger.error(f"[执行] 工作流执行失败：{e}")
        return {
            "query": query,
            "response": f"系统处理失败：{str(e)}",
            "error": str(e),
            "execution_path": ["start", "error"],
        }


def get_graph_info() -> Dict[str, Any]:
    """
    获取工作流信息（用于调试和展示）
    
    Returns:
        工作流配置信息
    """
    return {
        "architecture": "Supervisor Pattern (监督者模式)",
        "nodes": {
            NodeName.SUPERVISOR: "LLM 动态决策路由",
            NodeName.MEDICAL_HANDLER: "医疗问题处理",
            NodeName.CHAT_HANDLER: "闲聊处理",
            NodeName.UNANSWERABLE_HANDLER: "敏感话题处理",
            NodeName.HEALTH_PLAN_HANDLER: "健康计划处理",
        },
        "flow": "START → SUPERVISOR → [条件路由] → [业务节点] → END",
        "routing_type": "LLM-Driven (非硬编码 if-else)",
    }
