"""
医疗 Agent 基础使用示例
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from core.llm.client import LLMClient
from core.intent.classifier import IntentClassifier
from core.intent.router import IntentRouter


def example_basic_chat():
    """基础聊天示例"""
    print("=" * 80)
    print("基础聊天示例")
    print("=" * 80)

    # 加载配置
    config = BaseConfig(env_file=".env.dev")
    llm_config = LLMConfig.from_env(config)

    # 初始化 LLM 客户端
    llm_client = LLMClient(llm_config)

    # 简单对话
    response = llm_client.simple_chat(
        prompt="你好，请介绍一下自己",
        system_prompt="你是一个友好的医疗助手"
    )

    print(f"AI: {response}")
    print()


def example_intent_recognition():
    """意图识别示例"""
    print("=" * 80)
    print("意图识别示例")
    print("=" * 80)

    # 初始化
    config = BaseConfig(env_file=".env.dev")
    llm_config = LLMConfig.from_env(config)
    llm_client = LLMClient(llm_config)
    classifier = IntentClassifier(llm_client)

    # 测试不同问题
    test_queries = [
        "孩子发烧了怎么办？",
        "你好",
        "帮我制定减肥计划",
    ]

    for query in test_queries:
        print(f"\n问题：{query}")
        result = classifier.classify(query)
        print(f"  意图：{result['intent'].value}")
        print(f"  置信度：{result['confidence']:.2%}")
        if result.get('sub_category'):
            print(f"  子分类：{result['sub_category'].value}")

    print()


def example_full_pipeline():
    """完整流程示例"""
    print("=" * 80)
    print("完整流程示例")
    print("=" * 80)

    # 初始化所有组件
    config = BaseConfig(env_file=".env.dev")
    llm_config = LLMConfig.from_env(config)
    llm_client = LLMClient(llm_config)

    # 初始化意图识别
    classifier = IntentClassifier(llm_client)
    router = IntentRouter(classifier, llm_client, retriever=None)

    # 处理用户查询
    query = "孩子发烧了怎么办？"
    print(f"\n用户：{query}")

    # 路由处理
    result = router.route(query)

    if result.get('success'):
        print(f"AI: {result.get('response', '')[:200]}...")
        print(f"\n意图：{result.get('intent').value}")
        print(f"置信度：{result.get('confidence', 0):.2%}")
    else:
        print(f"处理失败：{result.get('message')}")

    print()


def main():
    """主函数"""
    print("\n医疗 Agent 使用示例\n")

    # 示例 1：基础聊天
    example_basic_chat()

    # 示例 2：意图识别
    example_intent_recognition()

    # 示例 3：完整流程
    example_full_pipeline()

    print("=" * 80)
    print("示例运行完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
