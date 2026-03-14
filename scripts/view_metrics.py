"""
产品经理数据面板
查看产品关键指标和数据分析
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.metrics import MetricsCollector
from utils.log_utils import setup_logger

setup_logger(level="INFO")


def print_daily_report(collector: MetricsCollector, date: str = None):
    """打印每日数据报告"""

    metrics = collector.get_daily_metrics(date)

    print("\n" + "=" * 80)
    print(f"📊 产品数据日报 - {metrics['date']}")
    print("=" * 80)

    # LLM 指标
    print("\n🤖 LLM 调用指标")
    print("-" * 80)
    llm = metrics["llm"]
    print(f"总调用次数：{llm['total_calls']}")
    print(f"成功次数：{llm['success_calls']}")
    print(f"失败次数：{llm['failed_calls']}")
    print(f"✅ 成功率：{llm['success_rate']:.1f}%")
    print(f"📝 总 Token 数：{llm['total_tokens']}")
    print(f"⏱️ 平均响应时间：{llm['avg_response_time']:.2f}秒")

    # RAG 指标
    print("\n📚 RAG 检索指标")
    print("-" * 80)
    rag = metrics["rag"]
    print(f"总检索次数：{rag['total_retrievals']}")
    print(f"成功次数：{rag['success_retrievals']}")
    print(f"✅ 命中率：{rag['hit_rate']:.1f}%")
    print(f"📄 平均结果数：{rag['avg_results_count']:.1f}个")
    print(f"⏱️ 平均响应时间：{rag['avg_response_time']:.2f}秒")

    # 意图识别指标
    print("\n🎯 意图识别指标")
    print("-" * 80)
    intent = metrics["intent"]
    print(f"总识别次数：{intent['total_classifications']}")
    print(f"平均置信度：{intent['avg_confidence']:.2f}")
    print(f"高置信度比例：{intent['high_confidence_rate']:.1f}%")

    if intent["intent_distribution"]:
        print("\n意图分布：")
        for intent_type, count in sorted(
            intent["intent_distribution"].items(), key=lambda x: x[1], reverse=True
        ):
            percentage = count / intent["total_classifications"] * 100 if intent["total_classifications"] > 0 else 0
            print(f"  - {intent_type}: {count}次 ({percentage:.1f}%)")

    # 用户指标
    print("\n👥 用户指标")
    print("-" * 80)
    user = metrics["user"]
    print(f"总会话数：{user['total_sessions']}")
    print(f"独立用户数：{user['unique_users']}")

    # 质量评估
    print("\n📈 质量评估")
    print("-" * 80)

    # LLM 成功率评分
    if llm["success_rate"] >= 99:
        print(f"✅ LLM 调用成功率：优秀 ({llm['success_rate']:.1f}%)")
    elif llm["success_rate"] >= 95:
        print(f"⚠️ LLM 调用成功率：良好 ({llm['success_rate']:.1f}%)")
    else:
        print(f"❌ LLM 调用成功率：需改进 ({llm['success_rate']:.1f}%)")

    # RAG 命中率评分
    if rag["hit_rate"] >= 95:
        print(f"✅ RAG 检索命中率：优秀 ({rag['hit_rate']:.1f}%)")
    elif rag["hit_rate"] >= 85:
        print(f"⚠️ RAG 检索命中率：良好 ({rag['hit_rate']:.1f}%)")
    else:
        print(f"❌ RAG 检索命中率：需改进 ({rag['hit_rate']:.1f}%)")

    # 意图识别准确率评分
    if intent["high_confidence_rate"] >= 90:
        print(f"✅ 意图识别准确率：优秀 ({intent['high_confidence_rate']:.1f}%)")
    elif intent["high_confidence_rate"] >= 80:
        print(f"⚠️ 意图识别准确率：良好 ({intent['high_confidence_rate']:.1f}%)")
    else:
        print(f"❌ 意图识别准确率：需改进 ({intent['high_confidence_rate']:.1f}%)")

    # 响应时间评分
    avg_response = llm["avg_response_time"]
    if avg_response <= 3:
        print(f"✅ 平均响应时间：优秀 ({avg_response:.2f}秒)")
    elif avg_response <= 5:
        print(f"⚠️ 平均响应时间：良好 ({avg_response:.2f}秒)")
    else:
        print(f"❌ 平均响应时间：需改进 ({avg_response:.2f}秒)")

    print("\n" + "=" * 80)


def print_trend_report(collector: MetricsCollector, days: int = 7):
    """打印趋势报告"""

    print("\n" + "=" * 80)
    print(f"📈 数据趋势报告（最近{days}天）")
    print("=" * 80)

    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    dates.reverse()

    print(f"\n{'日期':<12} {'LLM 调用':<10} {'成功率':<10} {'RAG 检索':<10} {'命中率':<10}")
    print("-" * 80)

    for date in dates:
        metrics = collector.get_daily_metrics(date)
        llm_calls = metrics["llm"]["total_calls"]
        llm_success = metrics["llm"]["success_rate"]
        rag_calls = metrics["rag"]["total_retrievals"]
        rag_hit = metrics["rag"]["hit_rate"]

        print(f"{date:<12} {llm_calls:<10} {llm_success:<9.1f}% {rag_calls:<10} {rag_hit:<9.1f}%")

    print("=" * 80)


def main():
    """主函数"""
    print("\n🏥 医疗 Agent - 产品经理数据面板\n")

    collector = MetricsCollector()

    # 查看今日数据
    today = datetime.now().strftime("%Y-%m-%d")
    print_daily_report(collector, today)

    # 查看趋势
    print_trend_report(collector, 7)

    # 提示
    print("\n💡 提示：")
    print("  - 数据文件位置：data/metrics/")
    print("  - 查看历史数据：python scripts/view_metrics.py --date 2026-03-14")
    print("  - 导出数据：python scripts/view_metrics.py --export")
    print()


if __name__ == "__main__":
    main()
