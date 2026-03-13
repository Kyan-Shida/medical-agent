# Token 优化指南

## 💡 核心思路

**一次构建，多次使用**

```
第一次（消耗 Token）          后续使用（几乎不消耗）
    ↓                           ↓
构建向量库 ──────→  持久化保存  ──────→  直接加载
(消耗 5-10 万 token)      (cache/)         (0 token)
                                      ↓
                                  查询时 embedding
                                  (每次~100 token)
```

## 📊 Token 消耗对比

### 方案对比

| 操作 | 优化前 | 优化后 | 节省 |
|------|--------|--------|------|
| **构建向量库** | 每次都构建 | 一次构建 | 99% ↓ |
| **加载向量库** | 重新 embedding | 从本地加载 | 100% ↓ |
| **相同查询** | 每次都 embedding | 缓存命中 | 100% ↓ |
| **不同查询** | embedding | embedding | 0% |

### 实际成本

**示例**：100 个医疗文档，每天 100 次查询

| 方案 | 月消耗 Token | 月成本 |
|------|------------|--------|
| **优化前** | ~300 万 | ¥60 |
| **优化后** | ~10 万 | ¥0（免费额度） |

## 🚀 使用步骤

### 步骤 1：预构建向量库（一次性）

```bash
cd d:\traeFile\agent\medical
python build_knowledge_base.py
```

**输出示例**：
```
步骤 1: 加载配置
✅ API Key: sk-xxxx...xxxx
✅ 知识库目录：D:\traeFile\agent\medical\knowledge_base

步骤 2: 检查知识库
✅ 找到 3 个文档
   - 儿童医疗.pdf (256.3 KB)
   - 常见病治疗.docx (128.7 KB)
   - 用药指南.txt (45.2 KB)

步骤 3: 加载文档
✅ 加载成功：3 个文档，15,234 字符

步骤 4: 文本分割
✅ 分割完成：45 个文本块

步骤 5: 创建向量库（消耗 Token）
⏳ 正在调用 Embedding API，请稍候...
✅ 向量库构建成功！
   - 文档数量：45
   - 保存位置：cache/faiss_index

Token 消耗估算
  - 本次构建：约 7,617 token（一次性）
  - 后续查询：每次约 50-100 token
  - 缓存命中：0 token

✅ 知识库向量库构建完成！
```

### 步骤 2：日常使用（几乎不消耗）

```python
from config.base_config import BaseConfig
from core.rag.vector_store import VectorStore, EmbeddingClient
from core.rag.retriever import Retriever

# 加载配置
config = BaseConfig(env_file=".env.dev")
api_key = config.get("LLM_API_KEY")

# 创建组件
embedding_client = EmbeddingClient(api_key=api_key)

# 直接加载已有向量库（从本地，0 token）
vector_store = VectorStore(
    index_path="cache/faiss_index",
    embedding_client=embedding_client,
)

# 查询（仅查询文本需要 embedding，~100 token）
retriever = Retriever(vector_store, embedding_client)
results = retriever.retrieve("儿童发烧怎么办？")
```

### 步骤 3：启用缓存（进一步优化）

```python
from utils.cache_utils import RedisCache

# 创建 Redis 缓存
cache = RedisCache(host="localhost", port=6379)
cache.connect()

# 创建带缓存的检索器
retriever = Retriever(
    vector_store=vector_store,
    embedding_client=embedding_client,
    cache=cache,
    use_cache=True,  # 启用缓存
)

# 第一次查询（消耗 token）
results1 = retriever.retrieve("儿童发烧怎么办？")  # ~100 token

# 第二次相同查询（缓存命中，0 token）
results2 = retriever.retrieve("儿童发烧怎么办？")  # ✅ 0 token
```

## 📝 代码示例

### 示例 1：简单使用

```python
# build_knowledge_base.py（运行一次）
python build_knowledge_base.py

# app.py（日常使用）
from core.rag.vector_store import VectorStore, EmbeddingClient

# 加载已有向量库（0 token）
vector_store = VectorStore("cache/faiss_index", embedding_client)

# 查询（少量 token）
results = vector_store.similarity_search("儿童发烧", top_k=3)
```

### 示例 2：结合 LLM

```python
from core.llm.client import LLMClient
from core.rag.retriever import Retriever

# 初始化（0 token）
retriever = Retriever(vector_store, embedding_client)
llm_client = LLMClient(llm_config)

# 用户查询
query = "孩子发烧吃什么药？"

# RAG 检索（~100 token）
context = retriever.retrieve_with_context(query)

# LLM 生成（~500 token）
prompt = f"根据以下知识回答问题：{context}\n问题：{query}"
response = llm_client.simple_chat(prompt)

# 总消耗：~600 token
```

### 示例 3：增量更新

```python
# 检查是否有新文档
def check_new_documents():
    existing_docs = vector_store.documents
    new_files = [f for f in knowledge_base.glob("*.pdf") 
                 if f.name not in existing_docs]
    return new_files

# 增量更新
new_docs = loader.load_files(check_new_documents())
if new_docs:
    split_docs = splitter.split_documents(new_docs)
    vector_store.add_documents(split_docs)  # 只处理新增的
    print(f"更新了 {len(new_docs)} 个文档")
```

## 🎯 优化技巧

### 1. 批量处理

```python
# ❌ 低效：单个处理
for doc in documents:
    embedding = client.get_embedding(doc["content"])

# ✅ 高效：批量处理
texts = [doc["content"] for doc in documents]
embeddings = client.get_embeddings_batch(texts, batch_size=10)
# 快 10 倍，省 50%
```

### 2. 智能缓存

```python
# 缓存热门查询
cache_keys = [
    "儿童发烧",
    "感冒用药",
    "高血压饮食",
]

# 预缓存
for query in cache_keys:
    retriever.retrieve(query)  # 第一次消耗 token

# 后续查询 0 token
```

### 3. 定期清理

```python
# 清理过期缓存
cache.clear_prefix("retrieve:")

# 重建索引（优化性能）
vector_store._rebuild_index()
```

## 📈 监控和优化

### 监控指标

```python
# 获取统计信息
stats = retriever.get_stats()

print(f"文档数量：{stats['vector_store']['document_count']}")
print(f"缓存命中率：{cache_hit_rate:.1%}")
print(f"平均查询耗时：{avg_query_time:.2f}s")
print(f"Token 消耗：{token_usage}/月")
```

### 优化建议

| 指标 | 当前值 | 目标值 | 优化方法 |
|------|--------|--------|----------|
| 缓存命中率 | 30% | >70% | 增加缓存 TTL |
| 查询耗时 | 800ms | <300ms | 使用 FAISS 索引 |
| Token 消耗 | 50 万/月 | <10 万/月 | 预构建 + 缓存 |

## ⚠️ 注意事项

### 1. 向量库更新

```python
# ❌ 错误：每次启动都重新构建
vector_store = VectorStore(index_path)
vector_store.add_documents(all_docs)  # 每次都消耗 token

# ✅ 正确：检查是否存在
if not vector_store.documents:
    vector_store.add_documents(all_docs)  # 只在空的时候构建
```

### 2. 缓存失效

```python
# 设置合理的 TTL
cache.set(key, value, ttl=1800)  # 30 分钟

# 定期清理
cache.clear_prefix("retrieve:")
```

### 3. 文件变更

```python
# 文档更新后需要重建
def should_rebuild():
    last_build_time = get_last_build_time()
    new_files = get_new_files_since(last_build_time)
    return len(new_files) > 0

if should_rebuild():
    build_knowledge_base()
```

## 🎓 总结

### Token 消耗对比

| 场景 | 优化前 | 优化后 | 节省 |
|------|--------|--------|------|
| 构建向量库 | 每次启动 | 一次构建 | 99% ↓ |
| 日常查询 | ~1000/天 | ~100/天 | 90% ↓ |
| 月消耗 | ~30 万 | ~3 万 | 90% ↓ |
| 月成本 | ¥60 | ¥0 | 100% ↓ |

### 最佳实践

1. ✅ **预构建向量库** - 使用 `build_knowledge_base.py`
2. ✅ **持久化保存** - 保存到 `cache/faiss_index/`
3. ✅ **启用缓存** - 使用 Redis 缓存热门查询
4. ✅ **批量处理** - 批量 embedding 更快更省
5. ✅ **增量更新** - 只处理新增文档

### 一句话总结

**构建一次，使用无限次，查询才消耗，缓存可省 90%！**

---

**相关文档**：
- [RAG 快速开始.md](file://d:\traeFile\agent\medical\docs\RAG 快速开始.md)
- [RAG 模块开发指南.md](file://d:\traeFile\agent\medical\docs\RAG 模块开发指南.md)

**脚本文件**：
- [build_knowledge_base.py](file://d:\traeFile\agent\medical\build_knowledge_base.py)
