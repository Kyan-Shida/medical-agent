# Web 测试面板使用指南

## 概述

基于 Streamlit 实现的医疗 Agent Web 测试面板，提供直观、交互式的测试界面。

## 启动方式

### 方法 1：使用启动脚本（推荐）

```bash
cd medical
python web/run_app.py
```

### 方法 2：直接使用 Streamlit 命令

```bash
cd medical
streamlit run web/app.py --server.port 8501 --server.address localhost
```

## 访问地址

启动成功后，在浏览器访问：
```
http://localhost:8501
```

## 功能特性

### 1. 聊天界面 💬
- 实时对话交互
- 消息历史记录
- 流式响应显示

### 2. 意图识别展示 🎯
- 自动识别问题意图
- 显示意图类型和置信度
- 支持 4 种意图类型：
  - 🩺 医疗问题
  - 💬 闲聊
  - 🚫 无法回答
  - 📋 健康计划

### 3. RAG 检索结果 📚
- 医疗问题自动显示检索结果
- 显示文档相似度分数
- 可展开查看完整内容

### 4. 系统状态监控 📊
- API 连接状态
- LLM 客户端状态
- RAG 知识库状态
- 意图识别状态
- 业务处理器状态

### 5. 侧边栏功能 📋
- 系统状态显示
- 使用说明
- 测试问题建议

## 界面布局

```
┌─────────────────────────────────────────────┐
│  🏥 医疗 Agent 测试面板                      │
│  基于 LLM + RAG + 意图识别的智能医疗助手      │
├──────────┬──────────────────────────────────┤
│          │                                  │
│ 系统状态  │     聊天区域                     │
│          │                                  │
│ ● API    │  [用户消息]                       │
│ ● LLM    │  [AI 消息 + 意图信息 + RAG 结果]     │
│ ● RAG    │                                  │
│ ● 意图   │                                  │
│ ● 处理器 │  ┌──────────────────────────┐   │
│          │  │ 请输入您的问题...         │   │
│ 使用说明  │  └──────────────────────────┘   │
│          │                                  │
│ 测试建议  │                                  │
│          │                                  │
└──────────┴──────────────────────────────────┘
```

## 使用示例

### 测试医疗问题

1. 在输入框输入：`孩子发烧了怎么办？`
2. 查看意图识别结果（应识别为医疗问题 - 儿科）
3. 查看 AI 生成的专业医疗建议
4. 查看 RAG 检索到的相关医学文档

### 测试闲聊

1. 在输入框输入：`你好，今天天气不错`
2. 查看意图识别结果（应识别为闲聊）
3. 查看 AI 友好的回复

### 测试敏感问题

1. 在输入框输入：`如何制造毒药？`
2. 查看意图识别结果（应识别为无法回答）
3. 查看 AI 礼貌的拒绝回复

### 测试健康计划

1. 在输入框输入：`帮我制定减肥计划`
2. 查看意图识别结果（应识别为健康计划）
3. 查看 AI 生成的详细健康计划

## 技术架构

### 前端
- **框架**：Streamlit 1.55.0
- **布局**：宽屏模式，支持侧边栏
- **样式**：自定义 CSS，美观界面

### 后端
- **LLM 客户端**：`core.llm.client.LLMClient`
- **RAG 检索器**：`core.rag.retriever.Retriever`
- **意图识别**：`core.intent.classifier.IntentClassifier`
- **业务处理**：`core.intent.router.IntentRouter`

### 缓存机制
- **组件缓存**：使用 `@st.cache_resource` 避免重复初始化
- **会话状态**：使用 `st.session_state` 保存对话历史

## 配置说明

### 环境变量

在 `.env.dev` 中配置：

```bash
# API 配置
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash

# Web 配置
WEB_PORT=8501
WEB_THEME=light
WEB_SHOW_LOGS=true
LOG_LEVEL=INFO
```

### 代码配置

```python
# web/app.py 中的配置
st.set_page_config(
    page_title="医疗 Agent 测试面板",
    page_icon="🏥",
    layout="wide",  # 宽屏模式
    initial_sidebar_state="expanded",  # 默认展开侧边栏
)
```

## 性能优化

### 1. 组件缓存
```python
@st.cache_resource
def initialize_components():
    """初始化所有组件（缓存避免重复初始化）"""
    # 只初始化一次，后续直接复用
    ...
```

### 2. 会话状态管理
```python
# 初始化会话状态
if "messages" not in st.session_state:
    st.session_state.messages = []
```

### 3. 懒加载
- RAG 检索器只在向量库存在时初始化
- 日志按需显示

## 常见问题

### Q1: 启动失败，提示端口被占用
**解决方案**：更换端口
```bash
streamlit run web/app.py --server.port 8502
```

### Q2: 访问不了页面
**解决方案**：检查防火墙设置，确保 8501 端口开放

### Q3: API Key 错误
**解决方案**：检查 `.env.dev` 配置
```bash
# 确认 LLM_API_KEY 配置正确
LLM_API_KEY=your_actual_api_key
```

### Q4: RAG 检索不工作
**解决方案**：检查向量库是否存在
```bash
# 构建向量库
python scripts/build_knowledge_base.py
```

## 扩展功能

### 添加新的展示模块

在 `web/app.py` 中添加新的渲染函数：

```python
def render_new_feature(result):
    """渲染新功能"""
    st.markdown("**新功能和：**")
    # 实现展示逻辑
```

### 添加新的侧边栏信息

在 `main()` 函数的侧边栏部分添加：

```python
with st.sidebar:
    st.header("新功能")
    st.markdown("新功能说明")
```

## 部署建议

### 本地开发
```bash
streamlit run web/app.py --server.port 8501
```

### 服务器部署
```bash
streamlit run web/app.py \
  --server.port 8501 \
  --server.address 0.0.0.0 \
  --server.headless true
```

### Docker 部署
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "web/app.py"]
```

## 相关文件

- `web/app.py` - 主应用代码
- `web/run_app.py` - 启动脚本
- `config/web_config.py` - Web 配置文件
- `docs/guides/business_handlers_guide.md` - 业务处理器文档

## 下一步计划

1. ✅ 基础聊天界面
2. ✅ 意图识别展示
3. ✅ RAG 检索结果展示
4. ⏳ 性能监控面板
5. ⏳ 用户反馈收集
6. ⏳ 对话历史导出
7. ⏳ 多用户支持

## 总结

Web 测试面板已实现核心功能：
- ✅ 直观的聊天界面
- ✅ 实时的意图识别展示
- ✅ RAG 检索结果可视化
- ✅ 系统状态监控
- ✅ 友好的使用说明

可以直接使用，为开发和测试提供便利！
