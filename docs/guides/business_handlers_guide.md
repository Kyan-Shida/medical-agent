# 业务处理器使用指南

## 概述

业务处理器模块实现了 4 种意图类型的具体处理逻辑，是医疗 Agent 的核心执行单元。

## 架构设计

```
用户输入
    ↓
意图分类器 (IntentClassifier)
    ↓
意图路由器 (IntentRouter)
    ↓
业务处理器 (Handlers)
    ├─ MedicalHandler → 医疗问题处理
    ├─ ChatHandler → 闲聊对话
    ├─ UnanswerableHandler → 无法回答问题
    └─ HealthPlanHandler → 健康计划制定
```

## 处理器详解

### 1. MedicalHandler（医疗问题处理器）

**功能**：处理医疗健康相关问题，支持 RAG 知识库增强

**特性**：
- 支持儿科和普通医疗子分类
- 自动 RAG 检索相关医学知识
- 基于检索结果生成专业回答
- 检索失败自动降级为纯 LLM

**示例**：
```python
from core.intent.handlers import MedicalHandler

handler = MedicalHandler(llm_client, retriever)
result = handler.handle(
    query="孩子发烧了怎么办？",
    context={"sub_category": SubCategory.PEDIATRICS}
)

print(result["response"])  # AI 生成的医疗建议
print(result["has_rag_context"])  # 是否使用了 RAG
print(result["retrieved_docs"])  # 检索到的文档
```

**返回结构**：
```python
{
    "success": True,
    "intent": IntentType.MEDICAL,
    "sub_category": SubCategory.PEDIATRICS,
    "query": "孩子发烧了怎么办？",
    "response": "AI 生成的回答",
    "has_rag_context": True,
    "retrieved_docs": [...],
    "metadata": {...}
}
```

### 2. ChatHandler（闲聊处理器）

**功能**：处理日常对话、问候、感谢等闲聊场景

**特性**：
- 友好、幽默、温暖的对话风格
- 高温度参数（0.9）增加多样性
- 简洁自然的回复

**示例**：
```python
from core.intent.handlers import ChatHandler

handler = ChatHandler(llm_client)
result = handler.handle(
    query="你好，今天天气不错",
    context={}
)

print(result["response"])  # "嗨，你好呀！确实，今天的天气真是宜人呢..."
```

### 3. UnanswerableHandler（无法回答处理器）

**功能**：处理敏感、危险、违法等无法回答的问题

**特性**：
- 识别政治、色情、暴力、违法等敏感话题
- 礼貌、委婉地拒绝回答
- 引导用户提出医疗健康相关问题
- 支持 LLM 生成自然回复或标准回复

**示例**：
```python
from core.intent.handlers import UnanswerableHandler

handler = UnanswerableHandler(llm_client)
result = handler.handle(
    query="如何制造炸弹？",
    context={"reason": "匹配敏感关键词"}
)

print(result["response"])
# "抱歉，这个问题我暂时无法回答。
# 我是一个专注于医疗健康领域的助手..."
```

### 4. HealthPlanHandler（健康计划处理器）

**功能**：制定个性化健康计划、饮食计划、运动计划等

**特性**：
- 科学合理：基于营养学、运动医学
- 个性化：考虑用户需求
- 可行实用：容易执行
- 结构化输出：目标、饮食、运动、作息等

**示例**：
```python
from core.intent.handlers import HealthPlanHandler

handler = HealthPlanHandler(llm_client)
result = handler.handle(
    query="帮我制定一个减肥计划",
    context={}
)

print(result["response"])
# ### 健康减肥计划
# #### 1. 目标设定
# #### 2. 饮食计划
# #### 3. 运动计划
# ...
```

## 集成使用

### 通过路由器调用（推荐）

```python
from core.intent.classifier import IntentClassifier
from core.intent.router import IntentRouter
from core.llm.client import LLMClient
from core.rag.retriever import Retriever

# 初始化组件
llm_client = LLMClient(llm_config)
retriever = Retriever(vector_store, embedding_client)
classifier = IntentClassifier(llm_client)
router = IntentRouter(classifier, llm_client, retriever)

# 路由处理
result = router.route("孩子发烧了怎么办？")

if result["success"]:
    print(f"意图：{result['intent'].value}")
    print(f"回答：{result['response']}")
else:
    print(f"处理失败：{result['message']}")
```

### 直接调用处理器

```python
from core.intent.handlers import create_handlers

# 创建所有处理器
handlers = create_handlers(llm_client, retriever)

# 调用特定处理器
medical_handler = handlers[IntentType.MEDICAL]
result = medical_handler.handle(query, context)
```

## 配置选项

### RAG 增强

医疗处理器支持 RAG 知识库增强：

```python
# 有 RAG 检索器
retriever = Retriever(vector_store, embedding_client)
handler = MedicalHandler(llm_client, retriever)

# 无 RAG 检索器（降级为纯 LLM）
handler = MedicalHandler(llm_client, retriever=None)
```

### 日志记录

所有处理器都支持详细的日志记录：

```python
from utils.log_utils import setup_logger

setup_logger(level="INFO")  # 设置日志级别
```

## 错误处理

所有处理器都有完善的错误处理：

```python
result = handler.handle(query, context)

if not result["success"]:
    print(f"错误：{result['message']}")
    print(f"详情：{result.get('error')}")
```

## 测试

运行测试验证处理器功能：

```bash
cd medical
python tests/intent/test_handlers.py
```

## 最佳实践

1. **始终通过路由器调用**：让路由器处理意图分类和置信度检查
2. **提供 RAG 支持**：医疗问题优先使用 RAG 增强
3. **处理降级情况**：LLM 失败时提供友好的错误提示
4. **记录详细日志**：便于调试和监控
5. **验证返回结果**：检查 `success` 字段和响应结构

## 扩展处理器

添加新的处理器类型：

```python
from core.intent.handlers import MedicalHandler

class CustomHandler(MedicalHandler):
    def handle(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # 自定义处理逻辑
        result = super().handle(query, context)
        # 添加自定义处理
        result["custom_field"] = "custom_value"
        return result

# 注册到路由器
@router.register(IntentType.MEDICAL)
def handle_custom(query, context):
    handler = CustomHandler(llm_client, retriever)
    return handler.handle(query, context)
```

## 性能优化

1. **RAG 缓存**：检索结果可缓存避免重复检索
2. **批量处理**：多个查询可批量处理
3. **异步调用**：支持异步 LLM 调用（待实现）
4. **Token 优化**：控制提示长度节省 Token

## 相关文件

- `core/intent/handlers.py` - 处理器实现
- `core/intent/router.py` - 路由器实现
- `core/intent/classifier.py` - 分类器实现
- `tests/intent/test_handlers.py` - 处理器测试
