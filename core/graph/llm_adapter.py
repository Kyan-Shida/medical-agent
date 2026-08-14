"""
LLM 适配器桥接层
将现有 LLMClient 封装为 LangGraph 可直接使用的接口
避免对现有 LLMClient 进行任何修改
"""
from typing import Dict, List, Any, Optional
import json
from utils.log_utils import get_logger


class LLMAdapter:
    """
    LLM 适配器
    
    桥接现有 LLMClient 和 LangGraph 之间的调用：
    - 输入：LangGraph 状态 + 系统提示 + 用户提示
    - 输出：LLM 响应（字符串或 JSON）
    
    这样做的好处：
    1. 不修改现有 LLMClient 代码
    2. LangGraph 节点可以直接调用
    3. 统一错误处理和日志记录
    """
    
    def __init__(self, llm_client):
        """
        初始化适配器
        
        Args:
            llm_client: 现有的 LLMClient 实例
        """
        self.llm_client = llm_client
        self.logger = get_logger(__name__)
    
    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        发送聊天请求
        
        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            AI 回复文本
        """
        return self.llm_client.simple_chat(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    
    def chat_with_history(
        self,
        system_prompt: str,
        conversation_history: List[Dict[str, str]],
        current_query: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        带历史的聊天请求
        
        Args:
            system_prompt: 系统提示
            conversation_history: 对话历史 [{role, content}]
            current_query: 当前用户输入
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            AI 回复文本
        """
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": current_query})
        
        response = self.llm_client.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        
        try:
            return response["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as e:
            self.logger.error(f"响应解析失败：{e}")
            raise ValueError(f"LLM 响应解析失败：{e}")
    
    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        发送请求并解析 JSON 响应
        
        Args:
            system_prompt: 系统提示
            user_prompt: 用户提示
            temperature: 温度参数（低温度以保证 JSON 稳定）
        
        Returns:
            解析后的 JSON 字典
        """
        response_text = self.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
        )
        
        # 尝试提取 JSON
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                return json.loads(response_text)
                
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON 解析失败：{e}")
            return {
                "error": f"JSON 解析失败",
                "raw_response": response_text,
            }
