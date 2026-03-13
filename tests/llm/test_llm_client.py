"""
LLM 模块单元测试
"""

import pytest
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from core.llm.client import LLMClient
from core.llm.parser import ResponseParser, ParsedResponse
from core.llm.multi_round import ConversationManager, Conversation, Message
from utils.exception_utils import LLMCallError, LLMTimeoutError


class TestLLMConfig:
    """测试 LLM 配置"""

    def test_config_creation(self):
        """测试配置创建"""
        config = LLMConfig(
            api_key="test_key",
            base_url="https://test.com",
            model="glm-4-flash",
        )

        assert config.api_key == "test_key"
        assert config.base_url == "https://test.com"
        assert config.model == "glm-4-flash"
        assert config.max_tokens == 2048
        assert config.temperature == 0.7

    def test_config_validation(self):
        """测试配置验证"""
        # 有效配置
        config = LLMConfig(api_key="key", base_url="url", model="model")
        assert config.validate() is True

        # 无效配置（缺少 api_key）
        config = LLMConfig(api_key="", base_url="url", model="model")
        assert config.validate() is False

        # 无效配置（缺少 base_url）
        config = LLMConfig(api_key="key", base_url="", model="model")
        assert config.validate() is False

    def test_config_from_env(self):
        """测试从环境变量加载配置"""
        config = BaseConfig(env_file=".env.dev")  # 使用开发环境
        llm_config = LLMConfig.from_env(config)

        # 只验证配置是否有效，不检查具体值
        assert llm_config.api_key is not None
        assert len(llm_config.api_key) > 0
        assert llm_config.base_url is not None
        assert llm_config.model is not None

    def test_get_api_headers(self):
        """测试获取 API 请求头"""
        config = LLMConfig(api_key="test_key")
        headers = config.get_api_headers()

        assert headers["Authorization"] == "Bearer test_key"
        assert headers["Content-Type"] == "application/json"


class TestResponseParser:
    """测试响应解析器"""

    def test_parse_normal_response(self):
        """测试解析正常响应"""
        parser = ResponseParser()

        response_data = {
            "id": "test-123",
            "model": "glm-4-flash",
            "choices": [
                {
                    "message": {"role": "assistant", "content": "Hello, I'm fine."},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30,
            },
        }

        parsed = parser.parse(response_data)

        assert isinstance(parsed, ParsedResponse)
        assert parsed.content == "Hello, I'm fine."
        assert parsed.model == "glm-4-flash"
        assert parsed.total_tokens == 30
        assert parsed.is_valid is True

    def test_parse_empty_response(self):
        """测试解析空响应"""
        parser = ResponseParser()

        with pytest.raises(LLMCallError) as exc_info:
            parser.parse({})

        assert "响应数据为空" in str(exc_info.value.message)

    def test_parse_no_choices(self):
        """测试解析无 choices 的响应"""
        parser = ResponseParser()

        response_data = {"id": "test-123", "model": "glm-4-flash"}

        with pytest.raises(LLMCallError) as exc_info:
            parser.parse(response_data)

        assert "响应中无 choices" in str(exc_info.value.message)

    def test_parse_json_response(self):
        """测试解析 JSON 响应"""
        parser = ResponseParser()

        response_data = {
            "model": "glm-4-flash",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": '{"intent": "medical", "confidence": 0.95}',
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"total_tokens": 10},
        }

        result = parser.parse_json_response(response_data)

        assert result["intent"] == "medical"
        assert result["confidence"] == 0.95

    def test_parse_json_with_markdown(self):
        """测试解析带 markdown 的 JSON 响应"""
        parser = ResponseParser()

        response_data = {
            "model": "glm-4-flash",
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": '```json\n{"key": "value"}\n```',
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"total_tokens": 10},
        }

        result = parser.parse_json_response(response_data)

        assert result["key"] == "value"


class TestLLMClient:
    """测试 LLM 客户端"""

    def test_client_initialization(self):
        """测试客户端初始化"""
        config = LLMConfig(api_key="test_key", base_url="https://test.com")
        client = LLMClient(config)

        assert client.config == config
        assert client.parser is not None
        assert client.stats["total_requests"] == 0

    def test_build_payload(self):
        """测试构建请求体"""
        config = LLMConfig(api_key="test_key")
        client = LLMClient(config)

        messages = [{"role": "user", "content": "Hello"}]
        payload = client._build_payload(
            messages=messages,
            temperature=0.8,
            max_tokens=1000,
            stream=False,
        )

        assert payload["model"] == "glm-4-flash"
        assert payload["messages"] == messages
        assert payload["temperature"] == 0.8
        assert payload["max_tokens"] == 1000
        assert payload["stream"] is False

    def test_update_stats(self):
        """测试更新统计信息"""
        config = LLMConfig(api_key="test_key")
        client = LLMClient(config)

        # 成功请求
        client._update_stats(success=True, tokens=100, time=2.5)
        assert client.stats["successful_requests"] == 1
        assert client.stats["total_tokens"] == 100

        # 失败请求
        client._update_stats(success=False)
        assert client.stats["failed_requests"] == 1

    def test_get_stats(self):
        """测试获取统计信息"""
        config = LLMConfig(api_key="test_key")
        client = LLMClient(config)

        # 添加一些数据
        client._update_stats(success=True, tokens=100, time=2.0)
        client._update_stats(success=True, tokens=200, time=3.0)

        stats = client.get_stats()

        assert stats["total_requests"] == 2
        assert stats["successful_requests"] == 2
        assert stats["success_rate"] == 1.0
        assert stats["avg_time"] == 2.5
        assert stats["avg_tokens"] == 150.0


class TestConversation:
    """测试对话类"""

    def test_conversation_creation(self):
        """测试对话创建"""
        conv = Conversation(session_id="test-123")

        assert conv.session_id == "test-123"
        assert len(conv.messages) == 0
        assert conv.max_history_length == 20

    def test_add_message(self):
        """测试添加消息"""
        conv = Conversation(session_id="test-123")

        conv.add_message(role="user", content="Hello")
        conv.add_message(role="assistant", content="Hi there!")

        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"

    def test_get_messages(self):
        """测试获取消息"""
        conv = Conversation(session_id="test-123")

        conv.add_message(role="system", content="You are helpful")
        conv.add_message(role="user", content="Hello")
        conv.add_message(role="assistant", content="Hi")

        # 包含系统消息
        messages = conv.get_messages(include_system=True)
        assert len(messages) == 3
        assert messages[0]["role"] == "system"

        # 不包含系统消息
        messages = conv.get_messages(include_system=False)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"

    def test_message_limit(self):
        """测试消息数量限制"""
        conv = Conversation(session_id="test-123", max_history_length=5)

        # 添加 10 条消息
        for i in range(10):
            conv.add_message(role="user", content=f"Message {i}")

        # 应该只保留最后 5 条
        assert len(conv.messages) == 5
        assert "Message 5" in conv.messages[0].content

    def test_clear_history(self):
        """测试清空历史"""
        conv = Conversation(session_id="test-123")

        conv.add_message(role="user", content="Hello")
        conv.clear_history()

        assert len(conv.messages) == 0

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        conv = Conversation(session_id="test-123")
        conv.add_message(role="user", content="Hello")
        conv.add_message(role="assistant", content="Hi")

        # 序列化
        data = conv.to_dict()

        # 反序列化
        conv2 = Conversation.from_dict(data)

        assert conv2.session_id == conv.session_id
        assert len(conv2.messages) == len(conv.messages)
        assert conv2.messages[0].content == conv.messages[0].content


class TestConversationManager:
    """测试对话管理器"""

    def test_create_session(self):
        """测试创建会话"""
        manager = ConversationManager()

        conv = manager.create_session(
            session_id="test-123",
            system_prompt="You are helpful",
        )

        assert conv.session_id == "test-123"
        assert len(conv.messages) == 1  # 系统消息
        assert conv.messages[0].role == "system"

    def test_get_nonexistent_session(self):
        """测试获取不存在的会话"""
        manager = ConversationManager()

        conv = manager.get_session("nonexistent")

        assert conv is None

    def test_save_and_get_session(self):
        """测试保存和获取会话"""
        manager = ConversationManager()

        # 创建并保存
        conv = manager.create_session(session_id="test-123")
        conv.add_message(role="user", content="Hello")
        manager.save_session(conv)

        # 获取
        retrieved = manager.get_session("test-123")

        assert retrieved is not None
        assert retrieved.session_id == "test-123"
        assert len(retrieved.messages) == 1

    def test_delete_session(self):
        """测试删除会话"""
        manager = ConversationManager()

        # 创建并保存
        conv = manager.create_session(session_id="test-123")
        manager.save_session(conv)

        # 删除
        manager.delete_session("test-123")

        # 验证已删除
        retrieved = manager.get_session("test-123")
        assert retrieved is None

    def test_add_message(self):
        """测试添加消息"""
        manager = ConversationManager()

        # 创建会话
        conv = manager.create_session(session_id="test-123")
        manager.save_session(conv)

        # 添加消息
        success = manager.add_message(
            session_id="test-123",
            role="user",
            content="Hello",
        )

        assert success is True

        # 验证消息已添加
        conv = manager.get_session("test-123")
        assert len(conv.messages) == 1
        assert conv.messages[0].content == "Hello"

    def test_get_conversation_history(self):
        """测试获取对话历史"""
        manager = ConversationManager()

        # 创建会话并添加消息
        conv = manager.create_session(session_id="test-123")
        conv.add_message(role="user", content="Hello")
        conv.add_message(role="assistant", content="Hi")
        conv.add_message(role="user", content="How are you?")
        manager.save_session(conv)

        # 获取历史
        history = manager.get_conversation_history("test-123")

        assert len(history) == 3
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Hello"


class TestIntegration:
    """集成测试"""

    @pytest.mark.skip(reason="需要真实的 API Key")
    def test_real_api_call(self):
        """测试真实 API 调用"""
        config = BaseConfig(env_file=".env.test")
        llm_config = LLMConfig.from_env(config)
        client = LLMClient(llm_config)

        # 测试连接
        if not client.test_connection():
            pytest.skip("API 连接失败")

        # 发送消息
        response = client.simple_chat("你好，请简单回复")

        assert len(response) > 0
        assert isinstance(response, str)

    def test_full_conversation_flow(self):
        """测试完整对话流程"""
        # 创建管理器
        manager = ConversationManager()

        # 创建会话
        conv = manager.create_session(
            session_id="flow-test",
            system_prompt="你是一个医疗助手",
        )
        manager.save_session(conv)

        # 模拟对话
        manager.add_message("flow-test", role="user", content="我感冒了怎么办？")
        manager.add_message(
            "flow-test", role="assistant", content="建议多休息，多喝水"
        )
        manager.add_message("flow-test", role="user", content="需要吃药吗？")

        # 获取历史
        history = manager.get_conversation_history("flow-test")

        assert len(history) == 4  # system + 3 messages
        assert history[0]["role"] == "system"
        assert "医疗助手" in history[0]["content"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
