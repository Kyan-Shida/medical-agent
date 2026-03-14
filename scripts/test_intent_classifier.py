"""
测试意图分类器修复
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

def test_classifier():
    """测试意图分类器"""
    print("=" * 80)
    print("🧪 测试意图分类器")
    print("=" * 80)
    print()
    
    # 加载配置
    config = BaseConfig(env_file=".env.dev")
    llm_config = LLMConfig.from_env(config)
    llm_client = LLMClient(llm_config)
    
    # 创建分类器
    classifier = IntentClassifier(llm_client)
    
    # 测试用例
    test_cases = [
        ("孩子发烧了怎么办？", "medical"),
        ("帮我制定健康计划", "health_plan"),
        ("感冒了有哪些症状？", "medical"),
        ("有什么饮食建议吗？", "medical"),
        ("你好啊", "chat"),
    ]
    
    print("开始测试...")
    print()
    
    success_count = 0
    fail_count = 0
    
    for text, expected_intent in test_cases:
        try:
            result = classifier.classify(text)
            actual_intent = result.get("intent")
            confidence = result.get("confidence", 0)
            
            if actual_intent.value == expected_intent:
                print(f"✅ {text}")
                print(f"   意图：{actual_intent.value} ({confidence:.2f}) - 正确")
                success_count += 1
            else:
                print(f"❌ {text}")
                print(f"   预期：{expected_intent}, 实际：{actual_intent.value}")
                fail_count += 1
        except Exception as e:
            print(f"❌ {text}")
            print(f"   错误：{e}")
            fail_count += 1
        
        print()
    
    # 总结
    print("=" * 80)
    print(f"测试完成：成功 {success_count}/{len(test_cases)}")
    print(f"         失败 {fail_count}/{len(test_cases)}")
    print("=" * 80)
    
    return fail_count == 0

if __name__ == "__main__":
    success = test_classifier()
    sys.exit(0 if success else 1)
