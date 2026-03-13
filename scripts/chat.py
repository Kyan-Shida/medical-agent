"""
简单对话测试脚本
用于快速测试 LLM 对话功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from core.llm.client import LLMClient
from core.llm.multi_round import ConversationManager
from utils.log_utils import setup_logger, get_logger


def simple_chat():
    """简单对话模式（无历史）"""
    logger = get_logger(__name__)
    
    print("=" * 60)
    print("医疗 Agent - 简单对话模式")
    print("=" * 60)
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'clear' 清空屏幕")
    print("=" * 60)
    print()
    
    # 加载配置
    config = BaseConfig(env_file=".env.dev")
    llm_config = LLMConfig.from_env(config)
    
    # 验证配置
    if not llm_config.validate():
        print("❌ 错误：LLM 配置无效，请检查 .env.dev 文件中的 API Key")
        return
    
    # 创建客户端
    client = LLMClient(llm_config)
    
    # 测试连接
    print("正在测试 API 连接...")
    if not client.test_connection():
        print("❌ API 连接失败，请检查网络和 API Key")
        return
    print("✅ API 连接成功")
    print()
    
    # 对话循环
    while True:
        try:
            # 获取用户输入
            user_input = input("您：").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("再见！")
                break
            
            if user_input.lower() == 'clear':
                import os
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
            
            # 调用 LLM
            print("AI:", end=" ", flush=True)
            
            # 使用系统提示
            system_prompt = "你是一个专业的医疗助手，提供专业、友好、安全的医疗建议。对于严重的医疗问题，建议用户咨询线下医生。"
            
            response = client.simple_chat(user_input, system_prompt=system_prompt)
            
            print(response)
            print()
            
        except KeyboardInterrupt:
            print("\n\n对话中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")
            break


def multi_round_chat():
    """多轮对话模式（带历史）"""
    logger = get_logger(__name__)
    
    print("=" * 60)
    print("医疗 Agent - 多轮对话模式")
    print("=" * 60)
    print("输入 'quit' 或 'exit' 退出")
    print("输入 'history' 查看对话历史")
    print("输入 'clear' 清空历史")
    print("=" * 60)
    print()
    
    # 加载配置
    config = BaseConfig(env_file=".env.dev")
    llm_config = LLMConfig.from_env(config)
    
    # 验证配置
    if not llm_config.validate():
        print("❌ 错误：LLM 配置无效")
        return
    
    # 创建客户端和对话管理器
    client = LLMClient(llm_config)
    manager = ConversationManager()
    
    # 创建会话
    session_id = "default-session"
    system_prompt = "你是一个专业的医疗助手，提供专业、友好、安全的医疗建议。记住对话历史，提供连贯的回答。"
    
    conv = manager.create_session(
        session_id=session_id,
        system_prompt=system_prompt
    )
    manager.save_session(conv)
    
    print("✅ 会话已创建")
    print()
    
    # 对话循环
    while True:
        try:
            # 获取用户输入
            user_input = input("您：").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("再见！")
                break
            
            if user_input.lower() == 'history':
                history = manager.get_conversation_history(session_id)
                print("\n" + "=" * 60)
                print("对话历史：")
                print("=" * 60)
                for i, msg in enumerate(history, 1):
                    print(f"{i}. [{msg['role']}] {msg['content']}")
                print("=" * 60 + "\n")
                continue
            
            if user_input.lower() == 'clear':
                manager.delete_session(session_id)
                conv = manager.create_session(session_id=session_id, system_prompt=system_prompt)
                manager.save_session(conv)
                print("✅ 对话历史已清空\n")
                continue
            
            # 添加用户消息到历史
            manager.add_message(session_id, role="user", content=user_input)
            
            # 获取对话历史（用于 LLM 调用）
            messages = conv.get_messages()
            
            # 调用 LLM
            print("AI:", end=" ", flush=True)
            
            response = client.chat(messages=messages)
            
            print(response.content)
            print()
            
            # 添加 AI 回复到历史
            manager.add_message(session_id, role="assistant", content=response.content)
            manager.save_session(conv)
            
        except KeyboardInterrupt:
            print("\n\n对话中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")
            logger.exception("对话异常")
            break


def main():
    """主函数"""
    # 设置日志
    setup_logger(level="INFO")
    
    print("=" * 60)
    print("医疗 Agent - 对话测试")
    print("=" * 60)
    print()
    print("请选择对话模式：")
    print("1. 简单对话（无历史记录）")
    print("2. 多轮对话（带历史记录）")
    print()
    
    choice = input("请输入选择 (1/2): ").strip()
    
    if choice == '1':
        simple_chat()
    elif choice == '2':
        multi_round_chat()
    else:
        print("无效选择，使用简单对话模式")
        simple_chat()


if __name__ == "__main__":
    main()
