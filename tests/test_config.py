"""
测试配置模块
验证环境配置加载和 LLM 连接性
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent  # tests/ -> medical/
sys.path.insert(0, str(project_root))

from config.base_config import BaseConfig
from config.llm_config import LLMConfig
from core.llm.client import LLMClient
from utils.log_utils import setup_logger, get_logger


def test_config_loading():
    """测试配置加载"""
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("测试配置加载")
    logger.info("=" * 60)
    
    # 加载开发环境配置
    config = BaseConfig(env_file=".env.dev")
    logger.info(f"✅ 配置加载成功：{config.env_file}")
    logger.info(f"项目根目录：{config.PROJECT_ROOT}")
    logger.info(f"日志目录：{config.LOGS_DIR}")
    logger.info(f"缓存目录：{config.CACHE_DIR}")
    logger.info(f"知识库目录：{config.KNOWLEDGE_BASE_DIR}")
    
    # 加载 LLM 配置
    llm_config = LLMConfig.from_env(config)
    logger.info(f"LLM API Key: {'已设置' if llm_config.api_key else '未设置'}")
    logger.info(f"LLM Base URL: {llm_config.base_url}")
    logger.info(f"LLM Model: {llm_config.model}")
    logger.info(f"LLM Max Tokens: {llm_config.max_tokens}")
    logger.info(f"LLM Timeout: {llm_config.timeout}s")
    logger.info(f"LLM Max Retries: {llm_config.max_retries}")
    
    # 验证配置
    if llm_config.validate():
        logger.info("✅ LLM 配置验证通过")
    else:
        logger.warning("⚠️ LLM 配置验证失败，请检查环境变量")
    
    logger.info("=" * 60)
    return config, llm_config


def test_llm_connection(llm_config: LLMConfig):
    """测试 LLM 连接"""
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("测试 LLM API 连接")
    logger.info("=" * 60)
    
    if not llm_config.validate():
        logger.warning("⚠️ LLM 配置无效，跳过连接测试")
        return False
    
    try:
        # 创建客户端
        client = LLMClient(llm_config)
        logger.info("✅ LLM 客户端创建成功")
        
        # 测试连接
        logger.info("正在测试 API 连接...")
        if client.test_connection():
            logger.info("✅ API 连接测试通过")
            
            # 简单测试
            logger.info("发送测试消息...")
            response = client.simple_chat("你好，请用一句话介绍你自己")
            logger.info(f"✅ 回复：{response}")
            
            # 显示统计信息
            stats = client.get_stats()
            logger.info(f"统计信息：{stats}")
            
            return True
        else:
            logger.error("❌ API 连接测试失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败：{e}", exc_info=True)
        return False


def main():
    """主函数"""
    # 设置日志
    setup_logger(level="DEBUG")
    logger = get_logger(__name__)
    
    logger.info("🚀 医疗 Agent - 配置测试")
    logger.info("")
    
    # 测试配置加载
    config, llm_config = test_config_loading()
    logger.info("")
    
    # 测试 LLM 连接
    connection_ok = test_llm_connection(llm_config)
    logger.info("")
    
    # 总结
    logger.info("=" * 60)
    logger.info("测试总结")
    logger.info("=" * 60)
    logger.info(f"配置加载：✅ 通过")
    logger.info(f"LLM 连接：{'✅ 通过' if connection_ok else '❌ 失败'}")
    logger.info("")
    
    if connection_ok:
        logger.info("🎉 所有测试通过！LLM 模块已就绪。")
    else:
        logger.info("⚠️ LLM 连接失败，请检查 API Key 和网络连接。")
    
    logger.info("")


if __name__ == "__main__":
    main()
