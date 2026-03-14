# BOM 预防措施指南

## 📋 问题回顾

**BOM (Byte Order Mark)** 是 Unicode 字节顺序标记，在 UTF-8 文件中是可选的。但 Python 不支持源代码文件中的 BOM，会导致语法错误。

**错误示例**：
```
SyntaxError: invalid non-printable character U+FEFF
```

## ✅ 已配置的预防措施

### 1. Git 配置 - `.gitattributes` ✅

**文件位置**: `.gitattributes`

**作用**：强制 Git 使用 UTF-8 without BOM 编码

**配置内容**：
```gitattributes
# Python 文件
*.py text eol=lf working-tree-encoding=UTF-8

# Markdown 文件
*.md text eol=lf working-tree-encoding=UTF-8

# 配置文件
*.txt text eol=lf working-tree-encoding=UTF-8
*.json text eol=lf working-tree-encoding=UTF-8
*.yaml text eol=lf working-tree-encoding=UTF-8

# 环境变量文件
.env text eol=lf working-tree-encoding=UTF-8
```

**效果**：
- ✅ 提交时自动转换为 LF 行尾
- ✅ 检出时自动使用 UTF-8 without BOM
- ✅ 防止 Windows 记事本添加 BOM

### 2. VS Code 配置 ✅

**文件位置**: `.vscode/settings.json`

**配置内容**：
```json
{
  "files.encoding": "utf8",
  "files.eol": "\n",
  "files.insertFinalNewline": true,
  "files.trimTrailingWhitespace": true
}
```

**效果**：
- ✅ 默认使用 UTF-8 without BOM
- ✅ 统一使用 LF 行尾符
- ✅ 自动保存时清理空白字符

### 3. PyCharm 配置 ✅

**文件位置**: `.idea/encodings.xml`

**配置内容**：
```xml
<component name="Encoding" defaultCharsetForPropertiesFiles="UTF-8">
  <file url="PROJECT" charset="UTF-8" />
</component>
```

**效果**：
- ✅ 项目级别设置 UTF-8 编码
- ✅ 所有文件使用统一编码

## 🔧 编辑器配置指南

### VS Code

1. **打开设置** (`Ctrl + ,`)
2. **搜索** `files.encoding`
3. **设置为** `utf8`
4. **搜索** `files.eol`
5. **设置为** `\n`

**或者修改 `settings.json`**：
```json
{
  "files.encoding": "utf8",
  "files.eol": "\n"
}
```

### PyCharm / IntelliJ IDEA

1. **打开设置** (`Ctrl + Alt + S`)
2. **导航到**: Editor → File Encodings
3. **设置**：
   - Global Encoding: `UTF-8`
   - Project Encoding: `UTF-8`
   - Default encoding for properties files: `UTF-8`

**或者使用 `.idea/encodings.xml`**（已提供）

### Sublime Text

1. **打开设置** (`Ctrl + ,`)
2. **添加配置**：
```json
{
  "default_encoding": "UTF-8"
}
```

### Notepad++

1. **菜单**: 设置 → 首选项 → 新建
2. **选择**: UTF-8 without BOM
3. **点击**: 关闭

### Vim / Neovim

**添加到 `~/.vimrc` 或 `~/.config/nvim/init.vim`**：
```vim
set encoding=utf-8
set fileencoding=utf-8
set fileencodings=utf-8,gbk,latin1
```

## 📝 最佳实践

### 1. 新建文件时

**推荐方式**：
```bash
# Linux/Mac
touch newfile.py
echo '# coding: utf-8' > newfile.py

# Windows PowerShell
New-Item -Path "newfile.py" -ItemType "File"
```

**避免使用**：
- ❌ Windows 记事本（默认 UTF-8 with BOM）
- ❌ WordPad
- ❌ 旧版编辑器

### 2. 转换已有文件

**批量转换 BOM 文件**：
```bash
# 使用 Python 脚本
python scripts/clean_bom.py

# 使用 iconv (Linux/Mac)
find . -name "*.py" -exec iconv -f utf-8 -t utf-8 {} -o {} \;

# 使用 dos2unix
dos2unix *.py
```

**检查文件是否包含 BOM**：
```bash
# Linux/Mac
file -I filename.py

# Python
python -c "print(open('filename.py', 'rb').read()[:3] == b'\xef\xbb\xbf')"
```

### 3. Git 钩子预防

**`.git/hooks/pre-commit`**：
```bash
#!/bin/bash

# 检查 BOM 字符
echo "Checking for BOM characters..."
BOM_FILES=$(git diff --cached --name-only | grep '\.py$' | while read file; do
    if head -c 3 "$file" | grep -q $'\xef\xbb\xbf'; then
        echo "❌ Error: $file contains BOM"
        exit 1
    fi
done)

if [ $? -ne 0 ]; then
    echo "Please remove BOM from files before committing."
    echo "Run: python scripts/clean_bom.py"
    exit 1
fi

echo "✅ No BOM characters found"
exit 0
```

**使其可执行**：
```bash
chmod +x .git/hooks/pre-commit
```

## 🔍 检测工具

### 1. 单个文件检测

```bash
# Python 一行命令
python -c "content = open('file.py', 'rb').read(); print('Has BOM:', content.startswith(b'\xef\xbb\xbf'))"
```

### 2. 批量检测

```bash
# 查找所有包含 BOM 的 Python 文件
find . -name "*.py" -exec python -c "import sys; content = open(sys.argv[1], 'rb').read(); sys.exit(0 if not content.startswith(b'\xef\xbb\xbf') else 1)" {} \; -print
```

### 3. 使用项目脚本

```bash
# 运行清理脚本（同时检测和清理）
python scripts/clean_bom.py
```

## 📊 常见场景对比

| 场景 | 推荐做法 | 避免做法 |
|------|----------|----------|
| 新建 Python 文件 | VS Code/PyCharm | Windows 记事本 |
| 编辑配置文件 | VS Code/PyCharm | WordPad |
| 保存文件 | Ctrl+S (自动 UTF-8) | 另存为 (可能选错编码) |
| 批量转换 | `clean_bom.py` 脚本 | 手动逐个处理 |
| Git 提交 | pre-commit 钩子检查 | 直接提交 |

## ✅ 检查清单

### 项目初始化

- [x] 创建 `.gitattributes` 文件
- [x] 创建 `.vscode/settings.json`
- [x] 创建 `.idea/encodings.xml`
- [x] 创建 `scripts/clean_bom.py`
- [ ] 设置 Git pre-commit 钩子（可选）

### 日常开发

- [x] 使用推荐编辑器（VS Code/PyCharm）
- [x] 避免使用 Windows 记事本
- [x] 定期运行 `clean_bom.py` 检查
- [ ] 配置 Git 钩子自动检查

### 代码审查

- [ ] 检查新文件是否有 BOM
- [ ] 使用 `git diff` 查看编码变化
- [ ] 运行 `clean_bom.py` 确认

## 🎯 快速参考

### 如果再次遇到 BOM 问题

1. **立即修复**：
   ```bash
   python scripts/clean_bom.py
   ```

2. **检查编辑器配置**：
   - VS Code: 确认 `files.encoding` = `utf8`
   - PyCharm: 确认 File Encodings = `UTF-8`

3. **验证 Git 配置**：
   ```bash
   cat .gitattributes
   ```

4. **预防措施**：
   - 更换编辑器（推荐 VS Code/PyCharm）
   - 配置 Git 钩子自动检查

## 📚 相关资源

- [UTF-8 BOM 说明](https://en.wikipedia.org/wiki/Byte_order_mark)
- [Git Attributes 文档](https://git-scm.com/docs/gitattributes)
- [VS Code 编码设置](https://code.visualstudio.com/docs/editor/codebasics#_encoding)
- [PyCharm 编码设置](https://www.jetbrains.com/help/pycharm/configuring-encodings.html)

## 🎉 总结

**已配置的预防措施**：
- ✅ `.gitattributes` - Git 级别强制 UTF-8 without BOM
- ✅ `.vscode/settings.json` - VS Code 默认 UTF-8
- ✅ `.idea/encodings.xml` - PyCharm 默认 UTF-8
- ✅ `scripts/clean_bom.py` - 清理工具

**推荐做法**：
1. 使用现代编辑器（VS Code/PyCharm）
2. 不要使用 Windows 记事本编辑代码
3. 定期运行清理脚本检查
4. （可选）配置 Git pre-commit 钩子

**BOM 问题再也不会发生了！** 🎉

---

**创建时间**: 2026-03-14  
**状态**: ✅ 已完成配置
