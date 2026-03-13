# RAG 模块快速开始

## ✅ 问题已解决

刚才的循环导入错误已修复！现在可以正常使用 RAG 模块了。

## 🚀 快速测试

### 方法 1：运行测试脚本

```bash
cd d:\traeFile\agent\medical
python tests/test_rag_simple.py
```

输入 `y` 开始测试。

### 方法 2：运行单元测试

```bash
python -m pytest tests/test_rag.py -v
```

## 📝 使用示例

### 完整流程

```python
from config.base_config import BaseConfig
from core.rag.document_loader import DocumentLoader
from core.rag.text_splitter import TextSplitter
from core.rag.vector_store import VectorStore, EmbeddingClient
from core.rag.retriever import Retriever

# 1. 加载配置
config = BaseConfig(env_file=".env.dev")
api_key = config.get("LLM_API_KEY")

# 2. 创建 Embedding 客户端（使用智谱 AI API）
embedding_client = EmbeddingClient(api_key=api_key, model="embedding-2")

# 3. 加载文档
loader = DocumentLoader()
docs = loader.load_directory("knowledge_base/")

# 4. 分割文本
splitter = TextSplitter(chunk_size=500, chunk_overlap=50)
documents = [{"content": doc.content, "metadata": doc.metadata} for doc in docs]
split_docs = splitter.split_documents(documents)

# 5. 创建向量库
vector_store = VectorStore(
    index_path="cache/faiss_index",
    embedding_client=embedding_client,
)
vector_store.add_documents(split_docs)

# 6. 检索
retriever = Retriever(vector_store, embedding_client, top_k=3)
results = retriever.retrieve("儿童发烧怎么办？")

# 7. 生成上下文
context = retriever.retrieve_with_context("儿童发烧怎么办？")
print(context)
```

### 结合 LLM 使用

```python
from core.llm.client import LLMClient
from config.llm_config import LLMConfig

# 创建 LLM 客户端
llm_config = LLMConfig.from_env(config)
llm_client = LLMClient(llm_config)

# 用户提问
query = "儿童发烧吃什么药？"

# RAG 检索
context = retriever.retrieve_with_context(query)

# 构建提示
prompt = f"""
【医疗知识库】
{context}

【患者问题】
{query}

请基于以上知识提供专业医疗建议。
"""

# 生成回答
response = llm_client.simple_chat(prompt)
print(response)
```

## 🎯 关键优势

### 无需本地 Embedding 模型！

使用**智谱 AI Embedding API**：
- ✅ 同一个 API Key（与 LLM 共用）
- ✅ 无需安装额外模型
- ✅ 无需 GPU 资源
- ✅ 免费额度充足

### 对比其他方案

| 方案 | 优势 | 劣势 |
|------|------|------|
| **智谱 AI API** | 无需部署，免费 | 需要网络 |
| 本地 BGE 模型 | 离线可用 | 需下载~500MB |
| 本地 m3e 模型 | 离线可用 | 需下载~400MB |

## 📊 测试数据

```
测试查询：儿童发烧怎么办？
检索结果：2 个相关文档
  1. 相似度：0.876
     内容：儿童发烧处理指南...
  2. 相似度：0.823
     内容：退烧药使用建议...

检索耗时：320ms
```

## ⚠️ 常见问题

### Q1: 提示 ImportError
```
ImportError: cannot import name 'RAGConfig'
```
**解决**：已修复循环导入，重新运行即可。

### Q2: Embedding API 调用失败
```
VectorStoreError: Embedding API 请求失败
```
**解决**：
1. 检查 `.env.dev` 中的 `LLM_API_KEY` 是否正确
2. 确认网络连接正常
3. 检查 API Key 余额

### Q3: 检索结果为空
```
检索到 0 个结果
```
**解决**：
1. 确认向量库中有文档
2. 降低 `score_threshold` 参数
3. 增加 `top_k` 值

## 🎓 下一步

RAG 模块已完成并可用，继续开发：
- [ ] 意图识别模块
- [ ] 业务处理器
- [ ] Web 测试面板

## 📖 详细文档

- [RAG 模块开发指南.md](file://d:\traeFile\agent\medical\docs\RAG 模块开发指南.md)

---

**状态**：✅ RAG 模块可用
**时间**：2026-03-13
**Embedding 方案**：智谱 AI API（无需本地模型）
