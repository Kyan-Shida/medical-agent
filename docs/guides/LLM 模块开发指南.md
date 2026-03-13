# LLM 模块开发指南

## 概述

LLM 模块是医疗 Agent 的核心组件，负责与 glm-4-5-flash 模型进行原生 API 调用，无 LangChain 绑定。

## 模块结构

```
core/llm/
├── __init__.py          # 模块初始化
├── client.py            # LLM 客户端（原生 API 调用）
├── parser.py            # 响应解析器
└── multi_round.py       # 多轮对话管理
```

## 核心组件

### 1. LLMClient - LLM 客户端

**位置**: [`core/llm/client.py`](file://d:\traeFile\agent\medical\core\llm\client.py)

**功能**:
- 原生 requests 调用 OpenAI 兼容 API
- 自动重试机制（指数退避）
- 响应统计和监控
- 降级处理

**使用示例**:

```python
from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from core.llm.client import LLMClient

# 加载配置
config = BaseConfig(env_file=".env.dev")
llm_config = LLMConfig.from_env(config)

# 创建客户端
client = LLMClient(llm_config)

# 简单聊天
response = client.simple_chat("你好，请问感冒了怎么办？")
print(response)

# 高级聊天（自定义参数）
messages = [
    {"role": "system", "content": "你是一个医疗助手"},
    {"role": "user", "content": "我发烧了"}
]
response = client.chat(
    messages=messages,
    temperature=0.7,
    max_tokens=1000
)
print(f"回复：{response.content}")
print(f"消耗 tokens: {response.total_tokens}")
print(f"耗时：{response.raw_response.get('response_time', 0):.2f}s")
```

**主要方法**:

| 方法 | 说明 | 参数 | 返回值 |
|------|------|------|--------|
| `chat` | 聊天接口 | messages, temperature, max_tokens, stream | ParsedResponse |
| `simple_chat` | 简单聊天 | prompt, system_prompt | str |
| `test_connection` | 测试连接 | 无 | bool |
| `get_stats` | 获取统计 | 无 | dict |

### 2. ResponseParser - 响应解析器

**位置**: [`core/llm/parser.py`](file://d:\traeFile\agent\medical\core\llm\parser.py)

**功能**:
- 解析 LLM API 响应
- 验证响应有效性
- 提取 JSON 格式内容
- 意图分类结果解析

**使用示例**:

```python
from core.llm.parser import ResponseParser

parser = ResponseParser()

# 解析普通响应
response_data = {...}  # API 响应
parsed = parser.parse(response_data)
print(f"内容：{parsed.content}")
print(f"模型：{parsed.model}")
print(f"有效：{parsed.is_valid}")

# 解析 JSON 响应
json_result = parser.parse_json_response(response_data)
print(f"意图：{json_result['intent']}")

# 解析意图分类
intent_result = parser.parse_intent_classification(response_data)
print(f"意图：{intent_result['intent']}")
print(f"置信度：{intent_result['confidence']}")
```

**ParsedResponse 数据结构**:

```python
@dataclass
class ParsedResponse:
    content: str              # 响应内容
    model: str                # 模型名称
    usage: Dict[str, int]     # token 使用统计
    finish_reason: str        # 结束原因
    total_tokens: int         # 总 token 数
    prompt_tokens: int        # 输入 token 数
    completion_tokens: int    # 输出 token 数
    raw_response: Dict        # 原始响应
    is_valid: bool            # 是否有效
    error_message: str        # 错误信息
```

### 3. ConversationManager - 多轮对话管理

**位置**: [`core/llm/multi_round.py`](file://d:\traeFile\agent\medical\core\llm\multi_round.py)

**功能**:
- 会话创建和管理
- 消息历史维护
- Redis 持久化存储
- 自动过期清理

**使用示例**:

```python
from core.llm.multi_round import ConversationManager
from utils.cache_utils import RedisCache

# 创建缓存连接
cache = RedisCache(host="localhost", port=6379)
cache.connect()

# 创建对话管理器
manager = ConversationManager(cache=cache, ttl=3600)

# 创建新会话
conv = manager.create_session(
    session_id="user-123",
    system_prompt="你是一个医疗助手"
)
manager.save_session(conv)

# 添加消息
manager.add_message(
    session_id="user-123",
    role="user",
    content="我感冒了怎么办？"
)

# 获取对话历史
history = manager.get_conversation_history("user-123")
for msg in history:
    print(f"{msg['role']}: {msg['content']}")

# 清空历史
manager.delete_session("user-123")
```

**Conversation 数据结构**:

```python
@dataclass
class Conversation:
    session_id: str                    # 会话 ID
    messages: List[Message]            # 消息列表
    created_at: float                  # 创建时间
    updated_at: float                  # 更新时间
    metadata: Dict[str, Any]           # 元数据
    max_history_length: int = 20       # 最大历史长度
```

## 配置说明

### LLM 配置项

在 `.env.dev` / `.env.test` / `.env.prod` 中配置：

```bash
# LLM API 配置
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash

# 请求参数
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7
LLM_TIMEOUT=30

# 重试配置
LLM_MAX_RETRIES=3
LLM_RETRY_DELAY=1.0
LLM_EXPONENTIAL_BACKOFF=true

# 降级配置
LLM_FALLBACK_MODEL=glm-4-flash
LLM_ENABLE_FALLBACK=true

# 缓存配置
LLM_ENABLE_CACHE=true
LLM_CACHE_TTL=3600
```

### 配置类

**LLMConfig**: [`config/llm_config.py`](file://d:\traeFile\agent\medical\config\llm_config.py)

```python
from config.base_config import BaseConfig
from config.llm_config import LLMConfig

# 从环境变量加载
config = BaseConfig(env_file=".env.dev")
llm_config = LLMConfig.from_env(config)

# 手动创建
llm_config = LLMConfig(
    api_key="your_key",
    base_url="https://open.bigmodel.cn/api/paas/v4",
    model="glm-4-flash",
    max_tokens=2048,
    temperature=0.7,
    timeout=30,
    max_retries=3
)

# 验证配置
if llm_config.validate():
    print("配置有效")

# 获取 API 请求头
headers = llm_config.get_api_headers()
```

## 异常处理

### 自定义异常

**位置**: [`utils/exception_utils.py`](file://d:\traeFile\agent\medical\utils\exception_utils.py)

```python
from utils.exception_utils import (
    LLMCallError,      # LLM 调用失败
    LLMTimeoutError,   # 超时
    LLMRateLimitError  # 限流
)

try:
    response = client.chat(messages)
except LLMTimeoutError as e:
    print(f"请求超时：{e.message}")
except LLMRateLimitError as e:
    print(f"请求限流：{e.message}")
except LLMCallError as e:
    print(f"调用失败：{e.message}")
```

### 重试机制

**位置**: [`utils/retry_utils.py`](file://d:\traeFile\agent\medical\utils\retry_utils.py)

LLMClient 内置重试机制：
- 最大重试次数：3 次
- 延迟策略：指数退避（1s, 2s, 4s...）
- 随机抖动：避免并发请求同步失败
- 触发条件：网络错误、超时、5xx 错误

## 测试

### 运行单元测试

```bash
cd d:\traeFile\agent\medical
python -m pytest tests/test_llm_client.py -v
```

### 运行配置测试

```bash
python tests/test_config.py
```

### 测试覆盖

- ✅ LLMConfig 配置创建和验证
- ✅ ResponseParser 响应解析
- ✅ LLMClient 客户端初始化
- ✅ Conversation 对话管理
- ✅ ConversationManager 会话管理
- ⏸️ 真实 API 调用（需要 API Key）

## 统计和监控

### 获取 LLM 统计信息

```python
stats = client.get_stats()
print(f"总请求数：{stats['total_requests']}")
print(f"成功请求数：{stats['successful_requests']}")
print(f"失败请求数：{stats['failed_requests']}")
print(f"成功率：{stats['success_rate']:.2%}")
print(f"平均耗时：{stats['avg_time']:.2f}s")
print(f"平均 tokens: {stats['avg_tokens']:.1f}")
print(f"总 tokens: {stats['total_tokens']}")
```

## 最佳实践

### 1. 会话管理

```python
# 为每个用户创建独立会话
session_id = f"user-{user_id}"
conv = manager.create_session(
    session_id=session_id,
    system_prompt="你是一个专业的医疗助手"
)
manager.save_session(conv)

# 每次对话后保存
manager.add_message(session_id, role="user", content=user_input)
# ... LLM 调用 ...
manager.add_message(session_id, role="assistant", content=response)
manager.save_session(conv)
```

### 2. 错误处理

```python
try:
    response = client.chat(messages, timeout=30)
    if response.is_valid:
        return response.content
    else:
        logger.warning(f"响应无效：{response.error_message}")
        return "抱歉，我暂时无法回答这个问题"
except LLMTimeoutError:
    logger.error("LLM 调用超时")
    return "请求超时，请稍后重试"
except LLMCallError as e:
    logger.error(f"LLM 调用失败：{e.message}")
    return "服务暂时不可用，请稍后重试"
```

### 3. 性能优化

```python
# 启用缓存
llm_config.enable_cache = True
llm_config.cache_ttl = 3600

# 限制历史长度
conv = Conversation(session_id="test", max_history_length=10)

# 使用连接池
client.session = requests.Session()
```

## 扩展指南

### 切换 LLM 模型

```python
# 修改配置文件
llm_config.model = "gpt-4"
llm_config.base_url = "https://api.openai.com/v1"

# 或动态切换
client.config.model = "glm-4"
```

### 自定义重试策略

```python
from utils.retry_utils import retry_with_backoff

@retry_with_backoff(
    max_retries=5,
    base_delay=0.5,
    max_delay=30.0,
    exponential=True
)
def custom_llm_call():
    ...
```

## 故障排查

### 常见问题

1. **API Key 无效**
   - 检查 `.env` 文件中的 `LLM_API_KEY` 是否正确
   - 确认 API Key 没有多余空格

2. **连接超时**
   - 检查网络连接
   - 增加 `LLM_TIMEOUT` 配置
   - 检查 API 服务状态

3. **响应解析失败**
   - 查看原始响应 `response.raw_response`
   - 检查 API 返回格式是否变化

### 日志查看

```bash
# 查看应用日志
tail -f logs/app.log

# 查看错误日志
tail -f logs/error_app.log.zip
```

## 下一步

LLM 模块已完成，继续开发：
- [ ] RAG 模块（文档加载/文本分割/向量检索）
- [ ] 意图识别模块（分类器 + 路由器）
- [ ] 业务处理器（医疗/闲聊/健康计划）
- [ ] Web 测试面板

## 参考文档

- [智谱 AI API 文档](https://open.bigmodel.cn/dev/api)
- [OpenAI Chat API](https://platform.openai.com/docs/api-reference/chat)
- [requests 库文档](https://docs.python-requests.org/)
- [tenacity 重试库](https://tenacity.readthedocs.io/)
