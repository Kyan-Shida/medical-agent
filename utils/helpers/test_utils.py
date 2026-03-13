"""
测试工具模块
"""

import time
from typing import Any, Dict, List
from unittest.mock import Mock
import json


def mock_llm_response(content: str, model: str = "test-model") -> Dict[str, Any]:
    """创建模拟的 LLM 响应"""
    return {
        "id": "test-123",
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": len(content.split()),
            "total_tokens": 10 + len(content.split()),
        },
    }


def mock_intent_response(intent: str, confidence: float = 0.95) -> Dict[str, Any]:
    """创建模拟的意图识别响应"""
    return {
        "id": "test-intent-123",
        "model": "test-model",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": json.dumps({
                        "intent": intent,
                        "confidence": confidence,
                        "reason": "Based on the input content",
                        "sub_category": None
                    }, ensure_ascii=False),
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 10,
            "total_tokens": 25,
        },
    }


def measure_execution_time(func, *args, **kwargs) -> tuple:
    """测量函数执行时间"""
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    execution_time = end_time - start_time
    return result, execution_time


def create_mock_client():
    """创建模拟的 LLM 客户端"""
    mock_client = Mock()
    mock_client.chat.return_value = Mock(
        content="Mock response",
        is_valid=True,
        total_tokens=10,
        model="mock-model"
    )
    return mock_client


def generate_test_messages(count: int = 5) -> List[Dict[str, str]]:
    """生成测试消息列表"""
    test_messages = []
    for i in range(count):
        test_messages.append({
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"Test message {i+1}"
        })
    return test_messages


class TestTimer:
    """测试计时器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
    
    def stop(self):
        """停止计时"""
        self.end_time = time.time()
    
    def elapsed(self) -> float:
        """获取经过时间"""
        if self.start_time is None:
            return 0.0
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
