"""
GitHub 提交前检查脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.log_utils import setup_logger, get_logger

setup_logger(level="INFO")
logger = get_logger(__name__)


def check_file(filename: str, required: bool = True) -> bool:
    """检查文件是否存在"""
    filepath = project_root / filename
    exists = filepath.exists()
    
    if exists:
        logger.info(f"✅ {filename}")
        return True
    else:
        if required:
            logger.error(f"❌ {filename} - 必需文件缺失")
        else:
            logger.warning(f"⚠️ {filename} - 可选文件缺失")
        return False


def check_directory(dirname: str) -> bool:
    """检查目录是否存在"""
    dirpath = project_root / dirname
    exists = dirpath.exists() and dirpath.is_dir()
    
    if exists:
        logger.info(f"✅ {dirname}/")
        return True
    else:
        logger.error(f"❌ {dirname}/ - 目录缺失")
        return False


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("🔍 GitHub 提交前检查")
    logger.info("=" * 80)
    logger.info("")
    
    # 必需文件检查
    logger.info("📄 必需文件检查:")
    logger.info("-" * 80)
    required_files = [
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "requirements.txt",
        ".gitignore",
        ".env.example",
        "main.py",
    ]
    
    required_count = 0
    for filename in required_files:
        if check_file(filename):
            required_count += 1
    
    logger.info("")
    
    # 核心目录检查
    logger.info("📁 核心目录检查:")
    logger.info("-" * 80)
    core_dirs = [
        "config",
        "core",
        "utils",
        "web",
        "scripts",
        "tests",
        "examples",
        "docs",
    ]
    
    dir_count = 0
    for dirname in core_dirs:
        if check_directory(dirname):
            dir_count += 1
    
    logger.info("")
    
    # 核心模块检查
    logger.info("🔧 核心模块检查:")
    logger.info("-" * 80)
    core_modules = [
        "core/llm/client.py",
        "core/rag/retriever.py",
        "core/intent/classifier.py",
        "core/intent/handlers.py",
        "utils/exception_handler.py",
        "utils/log_enhanced.py",
    ]
    
    module_count = 0
    for filename in core_modules:
        if check_file(filename):
            module_count += 1
    
    logger.info("")
    
    # Web 面板检查
    logger.info("🌐 Web 面板检查:")
    logger.info("-" * 80)
    web_files = [
        "web/app.py",
        "web/run_app.py",
        "web/README.md",
    ]
    
    web_count = 0
    for filename in web_files:
        if check_file(filename):
            web_count += 1
    
    logger.info("")
    
    # 测试文件检查
    logger.info("🧪 测试文件检查:")
    logger.info("-" * 80)
    test_files = [
        "tests/test_config.py",
        "tests/test_integration.py",
        "scripts/test_connection.py",
    ]
    
    test_count = 0
    for filename in test_files:
        if check_file(filename):
            test_count += 1
    
    logger.info("")
    
    # 文档检查
    logger.info("📚 文档检查:")
    logger.info("-" * 80)
    doc_files = [
        "docs/guides/",
        "docs/api/",
        "docs/summaries/",
        "docs/bugfixes/",
        "docs/optimization/",
    ]
    
    doc_count = 0
    for dirname in doc_files:
        if check_directory(dirname):
            doc_count += 1
    
    logger.info("")
    
    # 总结
    logger.info("=" * 80)
    logger.info("📊 检查总结")
    logger.info("=" * 80)
    
    total_required = len(required_files)
    total_dirs = len(core_dirs)
    total_modules = len(core_modules)
    total_web = len(web_files)
    total_tests = len(test_files)
    total_docs = len(doc_files)
    
    logger.info(f"必需文件：{required_count}/{total_required}")
    logger.info(f"核心目录：{dir_count}/{total_dirs}")
    logger.info(f"核心模块：{module_count}/{total_modules}")
    logger.info(f"Web 面板：{web_count}/{total_web}")
    logger.info(f"测试文件：{test_count}/{total_tests}")
    logger.info(f"文档目录：{doc_count}/{total_docs}")
    
    all_good = (
        required_count == total_required and
        dir_count == total_dirs and
        module_count == total_modules
    )
    
    logger.info("")
    
    if all_good:
        logger.info("✅ 所有检查通过！项目已准备好提交 GitHub")
        logger.info("")
        logger.info("下一步:")
        logger.info("  1. git init")
        logger.info("  2. git add .")
        logger.info("  3. git commit -m 'feat: 初始版本 v1.0.0'")
        logger.info("  4. git remote add origin <your-repo-url>")
        logger.info("  5. git push -u origin main")
    else:
        logger.error("❌ 部分检查未通过，请检查缺失的文件")
    
    logger.info("=" * 80)
    logger.info("")


if __name__ == "__main__":
    main()
