# 项目文件结构整理方案

## 当前问题

1. **文档分散** - docs 目录下文件过多，分类不清晰
2. **测试文件混乱** - tests 目录结构不够清晰
3. **缺少示例目录** - 示例代码和脚本混在一起
4. **配置文件分散** - 配置文件分布在多个位置

## 新的项目结构

```
medical/
├── .env.dev                    # 开发环境配置
├── .env.prod                   # 生产环境配置
├── .env.test                   # 测试环境配置
├── .gitignore                  # Git 忽略文件
├── README.md                   # 项目说明
├── requirements.txt            # 依赖包
├── main.py                     # 主入口
├── Dockerfile                  # Docker 配置
├── docker-compose.yml          # Docker Compose 配置
│
├── config/                     # 配置模块
│   ├── __init__.py
│   ├── base_config.py          # 基础配置
│   ├── llm_config.py           # LLM 配置
│   ├── rag_config.py           # RAG 配置
│   ├── web_config.py           # Web 配置
│   └── security_config.py      # 安全配置
│
├── core/                       # 核心业务逻辑
│   ├── __init__.py
│   ├── llm/                    # LLM 模块
│   │   ├── __init__.py
│   │   ├── client.py           # LLM 客户端
│   │   ├── parser.py           # 响应解析
│   │   └── multi_round.py      # 多轮对话
│   ├── rag/                    # RAG 模块
│   │   ├── __init__.py
│   │   ├── document_loader.py  # 文档加载
│   │   ├── text_splitter.py    # 文本分割
│   │   ├── vector_store.py     # 向量存储
│   │   └── retriever.py        # 检索器
│   ├── intent/                 # 意图识别模块
│   │   ├── __init__.py
│   │   ├── classifier.py       # 分类器
│   │   ├── router.py           # 路由器
│   │   └── handlers.py         # 业务处理器
│   └── health_check.py         # 健康检查
│
├── utils/                      # 工具模块
│   ├── __init__.py
│   ├── log_utils.py            # 日志工具
│   ├── log_enhanced.py         # 增强日志
│   ├── exception_utils.py      # 异常工具
│   ├── exception_handler.py    # 异常处理器
│   ├── retry_utils.py          # 重试工具
│   ├── cache_utils.py          # 缓存工具
│   └── security_utils.py       # 安全工具
│
├── web/                        # Web 测试面板
│   ├── __init__.py
│   ├── app.py                  # Streamlit 应用
│   ├── run_app.py              # 启动脚本
│   └── README.md               # Web 面板说明
│
├── scripts/                    # 工具脚本
│   ├── build_knowledge_base.py # 构建知识库
│   ├── chat.py                 # 命令行聊天
│   └── test_connection.py      # 连接测试
│
├── tests/                      # 测试文件
│   ├── __init__.py
│   ├── conftest.py             # pytest 配置
│   ├── test_config.py          # 配置测试
│   ├── test_integration.py     # 集成测试
│   ├── llm/                    # LLM 测试
│   │   ├── __init__.py
│   │   ├── test_llm_client.py
│   │   └── test_llm_parser.py
│   ├── rag/                    # RAG 测试
│   │   ├── __init__.py
│   │   ├── test_document_loader.py
│   │   ├── test_text_splitter.py
│   │   ├── test_vector_store.py
│   │   └── test_retriever.py
│   ├── intent/                 # 意图识别测试
│   │   ├── __init__.py
│   │   ├── test_classifier.py
│   │   ├── test_router.py
│   │   └── test_handlers.py
│   └── utils/                  # 工具测试
│       ├── __init__.py
│       ├── test_log_utils.py
│       └── test_exception_handler.py
│
├── examples/                   # 示例代码
│   ├── basic_usage.py          # 基础使用示例
│   ├── advanced_usage.py       # 高级使用示例
│   └── web_panel_demo.py       # Web 面板示例
│
├── docs/                       # 文档
│   ├── README.md               # 文档说明
│   ├── guides/                 # 使用指南
│   │   ├── llm_module.md       # LLM 模块指南
│   │   ├── rag_module.md       # RAG 模块指南
│   │   ├── intent_module.md    # 意图识别指南
│   │   ├── business_handlers.md # 业务处理器指南
│   │   └── web_panel.md        # Web 面板指南
│   ├── api/                    # API 文档
│   │   ├── llm_client.md
│   │   ├── retriever.md
│   │   └── classifier.md
│   ├── summaries/              # 总结文档
│   │   ├── llm_development.md
│   │   ├── rag_development.md
│   │   ├── business_handlers.md
│   │   └── web_panel.md
│   ├── bugfixes/               # Bug 修复记录
│   │   └── web_panel_null_check.md
│   └── optimization/           # 优化指南
│       └── token_optimization.md
│
├── knowledge_base/             # 知识库文件
│   └── 儿童医疗.docx
│
├── cache/                      # 缓存目录（自动生成）
│   ├── faiss_index/            # FAISS 向量索引
│   │   ├── documents.pkl
│   │   └── faiss.index
│   └── redis/                  # Redis 缓存（可选）
│
├── logs/                       # 日志目录（自动生成）
│   ├── app.log                 # 应用日志
│   └── error_app.log           # 错误日志
│
└── tmp/                        # 临时文件（自动生成）
    └── .gitkeep
```

## 目录说明

### 核心目录

- **config/** - 所有配置文件
- **core/** - 核心业务逻辑（LLM、RAG、意图识别）
- **utils/** - 通用工具模块
- **web/** - Web 测试面板
- **scripts/** - 工具脚本
- **tests/** - 测试文件（按模块分类）
- **examples/** - 示例代码
- **docs/** - 文档（分类清晰）

### 自动生成目录

- **cache/** - 缓存文件（向量库、Redis）
- **logs/** - 日志文件
- **tmp/** - 临时文件

## 文件迁移计划

### 1. 文档整理

```bash
# 移动现有文档到正确位置
docs/guides/
  - LLM 模块开发指南.md → guides/llm_module.md
  - RAG 模块开发指南.md → guides/rag_module.md
  - business_handlers_guide.md → guides/business_handlers.md
  - web_panel_guide.md → guides/web_panel.md

docs/summaries/
  - 保留所有总结文件

docs/bugfixes/
  - 保留所有 bug 修复记录

docs/optimization/
  - 保留所有优化文档
```

### 2. 测试文件整理

```bash
# 按模块分类测试文件
tests/llm/
  - test_llm_client.py (从 tests/llm/ 移动)

tests/rag/
  - test_rag.py → test_retriever.py
  - test_rag_simple.py (删除或合并)

tests/intent/
  - test_intent.py → test_classifier.py
  - test_handlers.py (已有)

tests/utils/
  - 新建测试文件
```

### 3. 创建示例目录

```bash
# 创建 examples 目录
examples/
  - basic_usage.py (基础使用示例)
  - advanced_usage.py (高级使用示例)
```

## 清理计划

### 删除不必要的文件

1. **__pycache__/** - Python 缓存（应加入 .gitignore）
2. **.pytest_cache/** - pytest 缓存（应加入 .gitignore）
3. **重复的文档** - 合并内容重复的文档
4. **过时的测试文件** - 删除不再使用的测试

### 更新 .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# 测试
.pytest_cache/
.coverage
htmlcov/

# 缓存
cache/
tmp/

# 日志
logs/
*.log

# 环境
.env
.venv
venv/

# IDE
.vscode/
.idea/
*.swp
*.swo
```

## 实施步骤

1. ✅ 创建新的目录结构
2. ⏳ 移动文件到新位置
3. ⏳ 更新导入路径
4. ⏳ 运行测试验证
5. ⏳ 更新文档引用
6. ⏳ 清理旧文件

## 注意事项

1. **保持向后兼容** - 确保移动文件后导入路径正确
2. **运行所有测试** - 验证文件移动后功能正常
3. **更新文档** - 更新所有文件路径引用
4. **备份重要文件** - 移动前备份关键文件

## 预期效果

- ✅ 项目结构清晰易懂
- ✅ 文档分类合理
- ✅ 测试组织有序
- ✅ 易于维护和扩展
