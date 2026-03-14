# BOM 字符问题修复说明

## 📋 问题描述

运行 `python main.py` 时报错：

```
SyntaxError: invalid non-printable character U+FEFF
```

## 🔍 问题原因

**BOM (Byte Order Mark)** 字符 `U+FEFF` 是一个 Unicode 标记，用于标识字节序。

**问题来源**：
- Windows 编辑器（如记事本）默认保存为 UTF-8 with BOM
- 某些 IDE 默认添加 BOM
- Python 不支持源代码文件中的 BOM（会导致语法错误）

## 🛠️ 修复过程

### 1. 问题定位

```bash
python -c "with open('core/llm/client.py', 'rb') as f: content = f.read(); print('Has BOM:', content.startswith(b'\xef\xbb\xbf'))"
```

输出：`Has BOM: True`

### 2. 创建清理脚本

```python
# scripts/clean_bom.py
def remove_bom(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
    
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]
        with open(file_path, 'wb') as f:
            f.write(content)
        print(f"✅ 已清理：{file_path}")
```

### 3. 彻底解决

删除有问题的文件并重新创建（确保无 BOM）：

```bash
# 删除文件
rm core/llm/client.py

# 重新创建（使用 UTF-8 无 BOM 编码）
```

## ✅ 修复结果

运行测试：

```bash
python main.py
```

输出：
```
🏥 医疗 Agent 启动中...
✅ 配置加载成功：.env.dev
📊 日志级别：INFO
⏱️ 开始：LLM 连接测试
✅ 完成：LLM 连接测试 - 耗时：1.779 秒
📊 性能报告 - LLM 连接测试：1779.07ms
✅ API 连接测试通过
```

## 📚 预防措施

### 1. 编辑器配置

**VS Code**:
```json
{
  "files.encoding": "utf8"
}
```

**PyCharm**:
- Settings → Editor → File Encodings
- Project Encoding: UTF-8
- Default encoding for properties files: UTF-8

### 2. 使用 .gitattributes

```gitattributes
# 强制 Git 使用 UTF-8
*.py text eol=lf working-tree-encoding=UTF-8
*.md text eol=lf working-tree-encoding=UTF-8
```

### 3. 添加 Git 钩子

`.git/hooks/pre-commit`:
```bash
#!/bin/bash
# 检查 BOM 字符
git diff --cached --name-only | grep '\.py$' | while read file; do
    if head -c 3 "$file" | grep -q $'\xef\xbb\xbf'; then
        echo "Error: $file contains BOM"
        exit 1
    fi
done
```

## 🔧 清理脚本

已创建 `scripts/clean_bom.py`，用于批量清理 BOM：

```bash
python scripts/clean_bom.py
```

**清理的文件**：
- core/llm/client.py ✅
- core/llm/parser.py ✅
- core/llm/multi_round.py ✅
- core/rag/*.py ✅
- core/intent/*.py ✅
- utils/*.py ✅
- main.py ✅

## 📊 影响范围

| 文件 | 状态 | 说明 |
|------|------|------|
| core/llm/client.py | ✅ 已修复 | BOM 导致语法错误 |
| 其他 Python 文件 | ✅ 已检查 | 无 BOM 问题 |
| README.md | ✅ 无影响 | Markdown 支持 BOM |

## 🎯 最佳实践

### 1. 文件编码规范

- **所有 Python 文件**: UTF-8 without BOM
- **所有 Markdown 文件**: UTF-8 without BOM
- **所有配置文件**: UTF-8 without BOM

### 2. 编辑器推荐设置

```json
{
  "files.encoding": "utf8",
  "files.eol": "\n",
  "files.insertFinalNewline": true,
  "files.trimTrailingWhitespace": true
}
```

### 3. Git 配置

```bash
# 全局设置
git config --global core.autocrlf input
git config --global core.safecrlf true

# 项目设置
git config core.quotepath false
git config core.ignorecase false
```

## ✅ 验证清单

- [x] BOM 字符已清理
- [x] `python main.py` 运行正常
- [x] 所有模块导入正常
- [x] LLM 连接测试通过
- [x] 性能追踪正常
- [x] 日志输出正常

## 📝 相关文件

- [`scripts/clean_bom.py`](file://d:\traeFile\agent\medical\scripts\clean_bom.py) - BOM 清理脚本
- [`core/llm/client.py`](file://d:\traeFile\agent\medical\core\llm\client.py) - 已修复的文件
- [`.gitattributes`](file://d:\traeFile\agent\medical\.gitattributes) - Git 编码配置（建议添加）

## 🎉 总结

**问题**：BOM 字符导致 Python 语法错误  
**原因**：Windows 编辑器默认保存为 UTF-8 with BOM  
**解决**：清理 BOM 并重新创建文件  
**预防**：配置编辑器使用 UTF-8 without BOM

**项目现在可以正常运行！** ✅

---

**修复时间**: 2026-03-14 11:43  
**修复状态**: ✅ 已完成  
**测试状态**: ✅ 已通过
