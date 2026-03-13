"""
医疗 Agent Web 测试面板
基于 Streamlit 实现的交互式测试界面
"""

import streamlit as st
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from config.web_config import WebConfig
from core.llm.client import LLMClient
from core.rag.vector_store import VectorStore, EmbeddingClient
from core.rag.retriever import Retriever
from core.intent.classifier import IntentClassifier, IntentType
from core.intent.router import IntentRouter
from utils.log_utils import setup_logger, get_logger

# 页面配置
st.set_page_config(
    page_title="医疗 Agent 测试面板",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义 CSS 样式
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #FFF3E0;
        border-left: 4px solid #FF9800;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #FFEBEE;
        border-left: 4px solid #F44336;
        margin: 1rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def initialize_components():
    """初始化所有组件（缓存避免重复初始化）"""
    # 设置日志
    setup_logger(level="INFO")
    logger = get_logger(__name__)

    # 加载配置
    config = BaseConfig(env_file=".env.dev")
    api_key = config.get("LLM_API_KEY")

    if not api_key:
        st.error("❌ 错误：请先配置 .env.dev 中的 LLM_API_KEY")
        return None

    # 初始化 LLM 客户端
    llm_config = LLMConfig.from_env(config)
    llm_client = LLMClient(llm_config)

    # 初始化 Embedding 客户端
    embedding_client = EmbeddingClient(api_key=api_key, model="embedding-2")

    # 初始化 RAG 检索器（如果向量库存在）
    retriever = None
    vector_store_path = config.CACHE_DIR / "faiss_index"

    if vector_store_path.exists():
        try:
            vector_store = VectorStore(
                index_path=str(vector_store_path),
                embedding_client=embedding_client,
            )
            retriever = Retriever(vector_store, embedding_client, top_k=3)
            rag_status = "✅ 已加载"
        except Exception as e:
            rag_status = f"⚠️ 加载失败：{e}"
    else:
        rag_status = "⚠️ 向量库不存在"

    # 初始化意图分类器
    classifier = IntentClassifier(llm_client)

    # 初始化意图路由器
    router = IntentRouter(classifier, llm_client, retriever)

    return {
        "config": config,
        "llm_client": llm_client,
        "embedding_client": embedding_client,
        "retriever": retriever,
        "classifier": classifier,
        "router": router,
        "rag_status": rag_status,
    }


def render_intent_info(intent_result):
    """渲染意图识别信息"""
    if not intent_result:
        return

    intent = intent_result.get("intent")
    confidence = intent_result.get("confidence", 0)
    sub_category = intent_result.get("sub_category")

    # 意图类型映射
    intent_names = {
        IntentType.MEDICAL: ("医疗问题", "🩺"),
        IntentType.CHAT: ("闲聊", "💬"),
        IntentType.UNANSWERABLE: ("无法回答", "🚫"),
        IntentType.HEALTH_PLAN: ("健康计划", "📋"),
    }

    intent_name, intent_icon = intent_names.get(intent, ("未知", "❓"))

    # 显示意图信息卡片
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.markdown(f"**{intent_icon} 意图类型：** {intent_name}")

    with col2:
        confidence_color = (
            "green" if confidence >= 0.8 else "orange" if confidence >= 0.6 else "red"
        )
        st.markdown(
            f"**置信度：** :{confidence_color}[{confidence:.2%}]"
        )

    with col3:
        if sub_category:
            st.markdown(f"**子分类：** {sub_category.value}")
        else:
            st.markdown("**子分类：** 无")


def render_rag_results(result):
    """渲染 RAG 检索结果"""
    if not result:
        return
    
    if not result.get("has_rag_context"):
        return

    retrieved_docs = result.get("retrieved_docs", [])
    if not retrieved_docs:
        return

    st.markdown("**📚 RAG 检索结果：**")

    for i, doc in enumerate(retrieved_docs, 1):
        content = doc.get("content", "")
        score = doc.get("score", 0)

        with st.expander(f"文档 {i} - 相似度：{score:.3f}"):
            st.text(content[:500] + "..." if len(content) > 500 else content)


def render_response(result):
    """渲染 AI 回答"""
    if not result.get("success"):
        st.error(f"❌ 处理失败：{result.get('message', '未知错误')}")
        return

    response = result.get("response", "")
    if not response:
        st.warning("⚠️ 没有生成回答")
        return

    # 显示回答
    st.markdown("**💬 AI 回答：**")
    st.markdown(response)

    # 显示元数据
    metadata = result.get("metadata", {})
    if metadata:
        with st.expander("📊 详细信息"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("回答长度", metadata.get("response_length", 0))
            with col2:
                st.metric("时间戳", metadata.get("timestamp", "N/A"))


def main():
    """主函数"""
    # 标题
    st.markdown('<h1 class="main-header">🏥 医疗 Agent 测试面板</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">基于 LLM + RAG + 意图识别的智能医疗助手</p>',
        unsafe_allow_html=True,
    )

    # 初始化组件
    components = initialize_components()

    if not components:
        st.stop()

    # 侧边栏 - 系统状态
    with st.sidebar:
        st.header("📊 系统状态")

        # API 状态
        api_key = components["config"].get("LLM_API_KEY")
        st.success(f"✅ API Key: {api_key[:10]}...{api_key[-8:]}")

        # LLM 状态
        st.success("✅ LLM 客户端：就绪")

        # RAG 状态
        if components["rag_status"].startswith("✅"):
            st.success(components["rag_status"])
        else:
            st.warning(components["rag_status"])

        # 意图识别状态
        st.success("✅ 意图识别：就绪")

        # 业务处理器状态
        st.success("✅ 业务处理器：就绪")

        st.divider()

        # 使用说明
        st.header("📖 使用说明")
        st.markdown(
            """
        1. **输入问题**：在下方输入框输入您的问题
        2. **查看意图**：系统会自动识别问题意图
        3. **获取回答**：AI 会生成专业回答
        4. **查看检索**：医疗问题会显示 RAG 检索结果
        """
        )

        st.divider()

        # 测试问题建议
        st.header("💡 测试问题建议")
        st.markdown(
            """
        - 🩺 医疗问题：孩子发烧了怎么办？
        - 💬 闲聊：你好，今天天气不错
        - 🚫 敏感问题：如何制造毒药？
        - 📋 健康计划：帮我制定减肥计划
        """
        )

    # 主界面 - 聊天区域
    st.divider()

    # 初始化会话状态
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 显示历史消息
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "intent" in message:
                render_intent_info(message["intent"])
            if "rag_results" in message:
                render_rag_results(message["rag_results"])

    # 聊天输入
    if prompt := st.chat_input("请输入您的问题..."):
        # 添加用户消息
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 处理 AI 响应
        with st.chat_message("assistant"):
            with st.spinner("正在思考..."):
                try:
                    # 路由处理
                    result = components["router"].route(prompt)

                    # 显示 AI 回答
                    if result.get("response"):
                        st.markdown(result["response"])

                        # 显示意图信息
                        render_intent_info(result)

                        # 显示 RAG 结果
                        render_rag_results(result)

                        # 保存消息到历史
                        message = {
                            "role": "assistant",
                            "content": result["response"],
                            "intent": {
                                "intent": result.get("intent"),
                                "confidence": result.get("confidence", 0),
                                "sub_category": result.get("sub_category"),
                            },
                        }
                        
                        # 只有当有 RAG 上下文时才添加 rag_results
                        if result.get("has_rag_context"):
                            message["rag_results"] = result
                        
                        st.session_state.messages.append(message)
                    else:
                        st.warning("⚠️ 没有生成回答")

                except Exception as e:
                    st.error(f"❌ 处理失败：{e}")
                    import traceback

                    st.code(traceback.format_exc())

    # 底部信息
    st.divider()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📦 核心模块：**")
        st.markdown("LLM | RAG | 意图识别 | 业务处理器")

    with col2:
        st.markdown("**🔧 技术栈：**")
        st.markdown("Streamlit | Python | FAISS | 智谱 AI")

    with col3:
        st.markdown("**📊 测试统计：**")
        user_messages = len(
            [m for m in st.session_state.messages if m["role"] == "user"]
        )
        st.markdown(f"对话轮数：{user_messages}")


if __name__ == "__main__":
    main()
