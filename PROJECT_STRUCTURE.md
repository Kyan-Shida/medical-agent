# 📁 项目结构总结

本文档说明项目的文件结构和组织方式。

---

## 🎯 整理成果

### 已删除的冗余文件

| 类型 | 文件/目录 | 原因 |
|------|---------|------|
| 临时文档 | `整理完成说明.md` | 项目整理临时文档 |
| 临时文档 | `docs/交互式菜单完成.md` | 功能开发完成文档 |
| 临时文档 | `docs/可靠启动方案完成.md` | 功能开发完成文档 |
| 临时文档 | `docs/启动方案更新完成.md` | 功能开发完成文档 |
| 临时文档 | `docs/数据面板集成完成.md` | 功能开发完成文档 |
| 临时文档 | `docs/文档中文化完成.md` | 文档整理临时文档 |
| 临时文档 | `docs/路径问题修复指南.md` | Bug 修复临时文档 |
| 临时文档 | `docs/项目整理说明.md` | 项目整理临时文档 |
| 临时数据 | `exports/` | 临时会话导出文件 |

**总计清理：** 9 个冗余文件/目录

### 保留的核心文档

**文档索引：**
- `docs/文档索引.md` - 所有文档的导航入口

**使用指南：**
- `docs/guides/快速启动指南.md`
- `docs/guides/环境配置指南.md`
- `docs/guides/业务处理器指南.md`
- `docs/guides/工业级 Web 前端指南.md`
- 等 10+ 个专业指南

**Bug 修复：**
- `docs/bugfixes/BOM 编码错误修复.md`
- `docs/bugfixes/Web 面板空值检查修复.md`
- `docs/bugfixes/意图分类器修复.md`

**优化指南：**
- `docs/optimization/Token 优化指南.md`
- `docs/optimization/Token 优化总结.md`

---

## 📂 完整项目结构

```
medical/
│
├── 📄 核心文件
│   ├── README.md                     # 项目主文档
│   ├── CHANGELOG.md                  # 更新日志
│   ├── LICENSE                       # MIT 许可证
│   ├── requirements.txt              # Python 依赖
│   ├── main.py                       # 主入口（交互式菜单）
│   ├── .env.example                  # 环境变量模板
│   ├── .gitignore                    # Git 忽略配置
│   ├── .gitattributes                # Git 属性
│   ├── Dockerfile                    # Docker 配置
│   ├── docker-compose.yml            # Docker Compose
│   ├── GITHUB_UPLOAD_GUIDE.md        # GitHub 上传指南 ⭐ 新增
│   └── PROJECT_STRUCTURE.md          # 项目结构说明 ⭐ 新增
│
├── ⚙️ 配置模块 (config/)
│   ├── __init__.py
│   ├── base_config.py                # 基础配置
│   ├── llm_config.py                 # LLM 配置
│   ├── rag_config.py                 # RAG 配置
│   ├── security_config.py            # 安全配置
│   └── web_config.py                 # Web 配置
│
├── 🧠 核心业务 (core/)
│   ├── __init__.py
│   ├── health_check.py               # 健康检查
│   │
│   ├── llm/                          # LLM 模块
│   │   ├── __init__.py
│   │   ├── client.py                 # LLM 客户端
│   │   ├── parser.py                 # 响应解析
│   │   └── multi_round.py            # 多轮对话
│   │
│   ├── rag/                          # RAG 模块
│   │   ├── __init__.py
│   │   ├── document_loader.py        # 文档加载
│   │   ├── text_splitter.py          # 文本分割
│   │   ├── vector_store.py           # 向量存储
│   │   └── retriever.py              # 检索器
│   │
│   └── intent/                       # 意图识别模块
│       ├── __init__.py
│       ├── classifier.py             # 分类器
│       ├── router.py                 # 路由器
│       └── handlers.py               # 业务处理器
│
├── 🛠️ 工具模块 (utils/)
│   ├── __init__.py
│   ├── log_utils.py                  # 日志工具
│   ├── log_enhanced.py               # 增强日志（性能追踪）
│   ├── exception_handler.py          # 异常处理器
│   ├── exception_utils.py            # 异常工具
│   ├── retry_utils.py                # 重试工具
│   ├── cache_utils.py                # 缓存工具
│   ├── metrics.py                    # 性能指标
│   └── security_utils.py             # 安全工具
│
├── 🌐 API 服务 (api/)
│   └── app.py                        # FastAPI 应用
│
├── 💻 Web 界面 (web/)
│   ├── app.py                        # Streamlit 应用（旧版）
│   ├── metrics_dashboard.py          # 数据面板
│   ├── run_api.py                    # API 启动脚本
│   ├── run_app.py                    # Streamlit 启动脚本
│   ├── run_metrics.py                # 数据面板启动脚本
│   ├── start_frontend.py             # React 前端启动脚本
│   ├── README.md                     # Web 说明
│   │
│   └── frontend/                     # React 前端项目
│       ├── public/
│       │   └── index.html
│       ├── src/
│       │   ├── api/
│       │   │   └── client.ts
│       │   ├── components/
│       │   │   ├── ChatInput.tsx
│       │   │   ├── ChatMessage.tsx
│       │   │   ├── Disclaimer.tsx
│       │   │   ├── LoadingState.tsx
│       │   │   ├── QuickTags.tsx
│       │   │   └── Sidebar.tsx
│       │   ├── types/
│       │   │   └── index.ts
│       │   ├── App.tsx
│       │   ├── index.css
│       │   └── index.tsx
│       ├── .env.example
│       ├── package.json
│       ├── tsconfig.json
│       ├── tailwind.config.js
│       └── postcss.config.js
│
├── 📜 工具脚本 (scripts/)
│   ├── build_knowledge_base.py       # 构建知识库
│   ├── chat.py                       # 命令行聊天
│   ├── check_github_ready.py         # GitHub 检查
│   ├── clean_bom.py                  # 清理 BOM
│   ├── test_connection.py            # 连接测试
│   ├── test_intent_classifier.py     # 意图分类器测试
│   └── verify_web.py                 # Web 验证
│
├── 🧪 测试文件 (tests/)
│   ├── __init__.py
│   ├── test_config.py                # 配置测试
│   ├── test_integration.py           # 集成测试
│   ├── test_optimization.py          # 优化测试
│   │
│   ├── intent/                       # 意图识别测试
│   │   ├── test_handlers.py
│   │   └── test_intent.py
│   │
│   ├── llm/                          # LLM 测试
│   │   └── test_llm_client.py
│   │
│   └── rag/                          # RAG 测试
│       ├── test_rag.py
│       └── test_rag_simple.py
│
├── 📖 示例代码 (examples/)
│   └── basic_usage.py                # 基础使用示例
│
├── 📚 文档 (docs/)
│   ├── 文档索引.md                   # 📚 文档导航
│   │
│   ├── guides/                       # 使用指南
│   │   ├── BOM 编码预防指南.md
│   │   ├── LLM 模块开发指南.md
│   │   ├── RAG 模块开发指南.md
│   │   ├── Web 数据面板指南.md
│   │   ├── Web 测试面板指南.md
│   │   ├── 业务处理器指南.md
│   │   ├── 产品经理指南.md
│   │   ├── 工业级 Web 前端指南.md
│   │   ├── 快速启动指南.md
│   │   └── 环境配置指南.md
│   │
│   ├── bugfixes/                     # Bug 修复记录
│   │   ├── BOM 编码错误修复.md
│   │   ├── Web 面板空值检查修复.md
│   │   └── 意图分类器修复.md
│   │
│   └── optimization/                 # 优化指南
│       ├── Token 优化指南.md
│       └── Token 优化总结.md
│
├── 📦 知识库 (knowledge_base/)       # 可选，大文件已忽略
│   └── *.docx, *.pdf, *.txt
│
├── 💾 缓存 (cache/)                  # 已忽略，自动生成
│   └── faiss_index/
│
└── 📝 日志 (logs/)                   # 已忽略，自动生成
    └── *.log
```

---

## 📊 目录统计

| 目录 | 文件数 | 说明 |
|------|-------|------|
| `config/` | 6 | 配置模块 |
| `core/` | 13 | 核心业务逻辑 |
| `utils/` | 9 | 工具模块 |
| `api/` | 1 | API 服务 |
| `web/` | 7 + frontend/ | Web 界面 |
| `scripts/` | 8 | 工具脚本 |
| `tests/` | 8 | 测试文件 |
| `examples/` | 1 | 示例代码 |
| `docs/` | 20+ | 文档 |

**总计：** 约 70+ 个核心文件

---

## 🔍 关键文件说明

### 入口文件

| 文件 | 用途 | 使用场景 |
|------|------|---------|
| `main.py` | 主入口 | 交互式菜单启动 |
| `web/run_api.py` | API 启动 | 单独启动 API 服务 |
| `web/start_frontend.py` | 前端启动 | 单独启动 React 前端 |
| `web/run_app.py` | Streamlit 启动 | 启动旧版 Web 面板 |
| `web/run_metrics.py` | 数据面板启动 | 启动产品经理数据面板 |

### 核心模块

| 模块 | 关键文件 | 功能 |
|------|---------|------|
| LLM | `core/llm/client.py` | LLM 调用、重试、降级 |
| RAG | `core/rag/retriever.py` | 知识检索、上下文构建 |
| 意图 | `core/intent/router.py` | 意图识别、路由分发 |
| 业务 | `core/intent/handlers.py` | 4 种业务处理器 |

### 配置文件

| 文件 | 用途 | 是否提交 |
|------|------|---------|
| `.env.example` | 配置模板 | ✅ 是 |
| `.env.dev` | 开发环境配置 | ❌ 否（敏感） |
| `.gitignore` | Git 忽略配置 | ✅ 是 |

---

## 🎯 文件查找指南

### 我想...

**修改 LLM 调用逻辑**
→ `core/llm/client.py`

**添加新的意图类型**
→ `core/intent/classifier.py` 和 `core/intent/handlers.py`

**修改 Web 界面**
→ `web/frontend/src/`

**调整 RAG 检索策略**
→ `core/rag/retriever.py` 和 `core/rag/vector_store.py`

**修改 API 接口**
→ `api/app.py`

**添加新的测试**
→ `tests/` 对应目录

**查看配置选项**
→ `config/` 对应配置文件

**查找使用文档**
→ `docs/文档索引.md`

---

## 📝 维护建议

### 定期清理

```bash
# 清理 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} +

# 清理日志
rm -rf logs/*.log

# 清理临时文件
rm -rf exports/
rm -rf *.tmp *.temp
```

### 文档更新

- 新增功能 → 更新 `README.md` 和 `docs/guides/`
- Bug 修复 → 添加 `docs/bugfixes/`
- 性能优化 → 添加 `docs/optimization/`
- 配置变更 → 更新 `.env.example`

### Git 提交规范

```bash
# 新功能
git commit -m "feat: 添加 xxx 功能"

# Bug 修复
git commit -m "fix: 修复 xxx 问题"

# 文档更新
git commit -m "docs: 更新 xxx 文档"

# 重构
git commit -m "refactor: 重构 xxx 模块"

# 性能优化
git commit -m "perf: 优化 xxx 性能"
```

---

## 🎊 整理完成

项目结构已完全整理，符合以下标准：

- ✅ **清晰**：目录结构明确，职责分明
- ✅ **简洁**：删除冗余文件，保留核心内容
- ✅ **规范**：命名统一，符合 Python/TypeScript 规范
- ✅ **完整**：文档齐全，便于维护和扩展
- ✅ **安全**：敏感文件已忽略，不会误提交

**准备就绪，可以上传 GitHub！** 🚀

---

**更新日期：** 2026-03-14  
**项目版本：** v1.0.0
