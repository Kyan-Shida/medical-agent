"""
医疗 Agent API 服务
基于 FastAPI 实现的 RESTful API
接受前端发出的api请求。
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uvicorn

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from core.llm.client import LLMClient
from core.rag.vector_store import VectorStore, EmbeddingClient
from core.rag.retriever import Retriever
from core.intent.classifier import IntentClassifier, IntentType
from core.intent.router import IntentRouter
from utils.log_utils import setup_logger, get_logger
from utils.exception_handler import handle_exception

# 初始化日志
setup_logger(level="INFO")
logger = get_logger(__name__)

# FastAPI 应用
app = FastAPI(
    title="医疗 Agent API",
    description="基于 LLM + RAG + 意图识别的智能医疗助手 API",
    version="1.0.0",
)

# CORS 配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求/响应模型
class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., description="用户消息", min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(None, description="会话 ID")


class Message(BaseModel):
    """消息模型"""
    role: str
    content: str
    intent: Optional[Dict[str, Any]] = None
    rag_results: Optional[List[Dict[str, Any]]] = None
    timestamp: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应模型"""
    success: bool
    message: Optional[Message] = None
    intent: Optional[Dict[str, Any]] = None
    rag_results: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    llm: bool
    rag: bool
    intent_classifier: bool


# 全局变量存储初始化组件
components = {}


@handle_exception(default_message="初始化失败")
def initialize_components():
    """初始化所有组件"""
    logger.info("🔧 开始初始化 API 组件...")
    
    # 加载配置
    config = BaseConfig(env_file=".env.dev")
    api_key = config.get("LLM_API_KEY")
    
    if not api_key:
        logger.error("❌ 错误：LLM_API_KEY 未配置")
        return None
    
    # 初始化 LLM 客户端
    llm_config = LLMConfig.from_env(config)
    llm_client = LLMClient(llm_config)
    logger.info("✅ LLM 客户端初始化成功")
    
    # 初始化 Embedding 客户端
    embedding_client = EmbeddingClient(api_key=api_key, model="embedding-2")
    logger.info("✅ Embedding 客户端初始化成功")
    
    # 初始化 RAG 检索器
    retriever = None
    vector_store_path = config.CACHE_DIR / "faiss_index"
    
    if vector_store_path.exists():
        try:
            vector_store = VectorStore(
                index_path=str(vector_store_path),
                embedding_client=embedding_client,
            )
            retriever = Retriever(vector_store, embedding_client, top_k=3)
            logger.info("✅ RAG 检索器初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ RAG 检索器初始化失败：{e}")
    else:
        logger.warning("⚠️ 向量库不存在，RAG 功能不可用")
    
    # 初始化意图分类器
    classifier = IntentClassifier(llm_client)
    logger.info("✅ 意图分类器初始化成功")
    
    # 初始化意图路由器
    router = IntentRouter(classifier, llm_client, retriever)
    logger.info("✅ 意图路由器初始化成功")
    
    return {
        "config": config,
        "llm_client": llm_client,
        "embedding_client": embedding_client,
        "retriever": retriever,
        "classifier": classifier,
        "router": router,
    }


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化组件"""
    global components
    components = initialize_components()
    
    if not components:
        logger.error("❌ 组件初始化失败，应用无法启动")
        sys.exit(1)
    
    logger.info("🎉 API 服务启动成功")


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    return HealthResponse(
        status="healthy",
        llm=True,
        rag=components.get("retriever") is not None,
        intent_classifier=True,
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口
    处理用户消息并返回 AI 回答
    """
    logger.info(f"📥 收到消息：{request.message[:50]}...")
    
    try:
        # 使用路由器处理消息
        result = components["router"].route(request.message)
        
        # 构建响应
        intent_info = {
            "type": result.get("intent").value if result.get("intent") else "unknown",
            "confidence": result.get("confidence", 0),
            "sub_category": result.get("sub_category").value if result.get("sub_category") else None,
        }
        
        rag_results = []
        if result.get("has_rag_context"):
            docs = result.get("retrieved_docs", [])
            rag_results = [
                {"content": doc.get("content", ""), "score": doc.get("score", 0)}
                for doc in docs
            ]
        
        message = Message(
            role="assistant",
            content=result.get("response", ""),
            intent=intent_info,
            rag_results=rag_results if rag_results else None,
        )
        
        logger.info(f"✅ 响应生成成功，意图：{intent_info['type']}")
        
        return ChatResponse(
            success=result.get("success", False),
            message=message,
            intent=intent_info,
            rag_results=rag_results if rag_results else None,
            metadata={
                "response_length": len(result.get("response", "")),
                "processing_time": result.get("processing_time", 0),
            },
        )
        
    except Exception as e:
        logger.error(f"❌ 聊天处理失败：{e}", exc_info=True)
        return ChatResponse(
            success=False,
            error=str(e),
        )


@app.get("/api/intent/types")
async def get_intent_types():
    """获取意图类型列表"""
    return {
        "types": [
            {"value": IntentType.MEDICAL.value, "label": "医疗问题", "icon": "🩺"},
            {"value": IntentType.CHAT.value, "label": "闲聊", "icon": "💬"},
            {"value": IntentType.UNANSWERABLE.value, "label": "无法回答", "icon": "🚫"},
            {"value": IntentType.HEALTH_PLAN.value, "label": "健康计划", "icon": "📋"},
        ]
    }


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("🚀 启动医疗 Agent API 服务")
    logger.info("=" * 80)
    
    # 从配置读取端口和地址
    config = BaseConfig(env_file=".env.dev")
    api_port = config.get_int("API_PORT", 8000)
    api_host = config.get("API_HOST", "localhost")
    
    logger.info(f"访问地址：http://{api_host}:{api_port}")
    logger.info("API 文档：http://{api_host}:{api_port}/docs")
    logger.info("=" * 80)
    
    uvicorn.run(
        app,
        host=api_host,
        port=api_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
