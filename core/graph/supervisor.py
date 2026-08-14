"""
监督者节点 (Supervisor Node)
使用 LLM 动态决策替代硬编码的 if-else 路由

核心思想：
- 原有 classifier.py + router.py 是硬编码路由
- 现在升级为由 LLM 扮演"监督者"角色，动态决定走哪条分支
- 监督者分析用户意图，输出路由决策（intent + next_node）
"""
from typing import Dict, Any
from core.graph.state import AgentState, NodeName, INTENT_TO_NODE_MAP, NODE_DESCRIPTIONS
from core.graph.llm_adapter import LLMAdapter
from utils.log_utils import get_logger

logger = get_logger(__name__)


class Supervisor:
    """
    监督者 - LLM 驱动的动态路由器
    
    相比原有硬编码路由的改进：
    1. 不再依赖 if-else 判断，而是由 LLM 做语义理解
    2. 可以处理更复杂的模糊意图
    3. 支持动态扩展新的意图类型
    4. 决策过程可解释（输出 reason 字段）
    """
    
    # 系统提示词 - 定义监督者的角色和任务
    SUPERVISOR_PROMPT = """你是一个医疗智能助手的"监督者"，负责分析用户意图并决定应该将请求路由到哪个处理器。

可用的处理器（节点）如下：
{node_descriptions}

你的任务：
1. 分析用户输入的真实意图
2. 决定最合适的处理节点
3. 输出 JSON 格式的决策结果

决策规则：
- medical_handler: 当用户询问医疗问题时（症状、疾病、用药、治疗等）
- chat_handler: 当用户只是闲聊时（问候、感谢、打招呼等）
- unanswerable_handler: 当问题涉及敏感话题或超出医疗范围时
- health_plan_handler: 当用户请求制定健康计划时（减肥、饮食、运动等）

对于医疗问题，还需要判断子分类：
- pediatrics: 涉及儿童的医疗问题
- general: 成人医疗问题或其他

请严格按照以下 JSON 格式返回：
{{
    "intent": "意图类型(medical/chat/unanswerable/health_plan)",
    "confidence": 0.0-1.0,
    "reason": "决策理由",
    "sub_category": "子分类(仅medical需要，pediatrics/general)",
    "next_node": "路由到的节点名称"
}}

示例：
输入："孩子发烧了怎么办？"
输出：{{"intent": "medical", "confidence": 0.98, "reason": "询问儿童发烧处理方法", "sub_category": "pediatrics", "next_node": "medical_handler"}}

输入："你好"
输出：{{"intent": "chat", "confidence": 0.99, "reason": "日常问候", "sub_category": null, "next_node": "chat_handler"}}

输入："如何制造毒药？"
输出：{{"intent": "unanswerable", "confidence": 0.95, "reason": "涉及危险内容", "sub_category": null, "next_node": "unanswerable_handler"}}

输入："帮我制定一个减肥计划"
输出：{{"intent": "health_plan", "confidence": 0.97, "reason": "请求制定健康计划", "sub_category": null, "next_node": "health_plan_handler"}}
"""
    
    def __init__(self, llm_adapter: LLMAdapter):
        """
        初始化监督者
        
        Args:
            llm_adapter: LLM 适配器实例
        """
        self.llm_adapter = llm_adapter
        self.logger = get_logger(__name__)
        
        # 格式化节点描述到提示词
        node_descriptions = "\n".join(
            f"- {name}: {desc}" 
            for name, desc in NODE_DESCRIPTIONS.items()
        )
        self.system_prompt = self.SUPERVISOR_PROMPT.format(
            node_descriptions=node_descriptions
        )
    
    def run(self, state: AgentState) -> AgentState:
        """
        执行监督者决策（LangGraph 节点入口）
        
        Args:
            state: 当前 Agent 状态
        
        Returns:
            更新后的状态（包含意图识别结果和路由决策）
        """
        query = state.get("query", "")
        conversation_history = state.get("conversation_history", [])
        
        self.logger.info(f"[监督者] 分析用户意图：{query[:50]}...")
        
        try:
            # 构建用户提示
            user_prompt = f'用户输入："{query}"'
            
            # 如果有对话历史，添加上下文
            if conversation_history:
                history_text = "\n".join(
                    f"{msg['role']}: {msg['content'][:100]}"
                    for msg in conversation_history[-5:]  # 最近5轮
                )
                user_prompt += f"\n\n对话历史：\n{history_text}"
            
            # 调用 LLM 获取决策
            decision = self.llm_adapter.chat_json(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.3,  # 低温度保证决策稳定性
            )
            
            # 解析决策结果
            intent = decision.get("intent", "chat")
            confidence = decision.get("confidence", 0.5)
            reason = decision.get("reason", "")
            sub_category = decision.get("sub_category")
            next_node = decision.get("next_node", INTENT_TO_NODE_MAP.get(intent, NodeName.CHAT_HANDLER))
            
            # 验证并修正 next_node
            if next_node not in INTENT_TO_NODE_MAP.values():
                self.logger.warning(f"[监督者] 无效的节点名称：{next_node}，使用默认路由")
                next_node = INTENT_TO_NODE_MAP.get(intent, NodeName.CHAT_HANDLER)
            
            # 置信度过低时降级到闲聊
            if confidence < 0.5:
                self.logger.warning(f"[监督者] 置信度过低：{confidence:.2f}，降级到闲聊")
                intent = "chat"
                next_node = NodeName.CHAT_HANDLER
                confidence = 0.5
                reason += " (置信度过低，降级处理)"
            
            self.logger.info(
                f"[监督者] 决策完成：{intent} -> {next_node} "
                f"(置信度：{confidence:.2f})"
            )
            
            # 更新状态
            state["intent"] = intent
            state["confidence"] = confidence
            state["reason"] = reason
            state["sub_category"] = sub_category
            state["next_node"] = next_node
            state["execution_path"] = state.get("execution_path", []) + [NodeName.SUPERVISOR]
            
        except Exception as e:
            self.logger.error(f"[监督者] 决策失败：{e}")
            # 失败时降级到闲聊
            state["intent"] = "chat"
            state["confidence"] = 0.3
            state["reason"] = f"监督者决策失败，降级处理：{str(e)}"
            state["next_node"] = NodeName.CHAT_HANDLER
            state["error"] = str(e)
            state["execution_path"] = state.get("execution_path", []) + [NodeName.SUPERVISOR]
        
        return state


def supervisor_node(state: AgentState, supervisor: Supervisor) -> AgentState:
    """
    监督者节点函数（LangGraph 调用入口）
    
    Args:
        state: 当前状态
        supervisor: 监督者实例
    
    Returns:
        更新后的状态
    """
    return supervisor.run(state)
