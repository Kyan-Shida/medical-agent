"""
清理 BOM 字符的脚本
"""

import os
from pathlib import Path

def remove_bom(file_path):
    """移除文件的 BOM 字符"""
    try:
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # 移除 UTF-8 BOM (EF BB BF)
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
            with open(file_path, 'wb') as f:
                f.write(content)
            print(f"✅ 已清理：{file_path}")
            return True
        else:
            print(f"⚠️ 无需清理：{file_path}")
            return False
    except Exception as e:
        print(f"❌ 清理失败 {file_path}: {e}")
        return False

def main():
    """主函数"""
    print("=" * 80)
    print("🧹 清理 BOM 字符")
    print("=" * 80)
    
    # 需要清理的文件
    files_to_clean = [
        "core/llm/client.py",
        "core/llm/parser.py",
        "core/llm/multi_round.py",
        "core/rag/document_loader.py",
        "core/rag/text_splitter.py",
        "core/rag/vector_store.py",
        "core/rag/retriever.py",
        "core/intent/classifier.py",
        "core/intent/router.py",
        "core/intent/handlers.py",
        "utils/exception_handler.py",
        "utils/log_enhanced.py",
        "main.py",
    ]
    
    project_root = Path(__file__).parent.parent
    cleaned = 0
    skipped = 0
    
    for file_name in files_to_clean:
        file_path = project_root / file_name
        if file_path.exists():
            if remove_bom(file_path):
                cleaned += 1
            else:
                skipped += 1
        else:
            print(f"⚠️ 文件不存在：{file_path}")
            skipped += 1
    
    print()
    print("=" * 80)
    print(f"清理完成：{cleaned} 个文件已清理，{skipped} 个文件跳过")
    print("=" * 80)

if __name__ == "__main__":
    main()
