"""测试 utils 导入"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("测试导入...")

try:
    from utils.logging.log_utils import get_logger
    print("✅ logging.log_utils")
except Exception as e:
    print(f"❌ logging.log_utils: {e}")

try:
    from utils.exceptions.exception_utils import BaseMedicalAgentError
    print("✅ exceptions.exception_utils")
except Exception as e:
    print(f"❌ exceptions.exception_utils: {e}")

try:
    from utils.helpers.retry_utils import retry_with_backoff
    print("✅ helpers.retry_utils")
except Exception as e:
    print(f"❌ helpers.retry_utils: {e}")

try:
    from utils.helpers.cache_utils import CacheManager
    print("✅ helpers.cache_utils")
except Exception as e:
    print(f"❌ helpers.cache_utils: {e}")

print("\n完成！")
