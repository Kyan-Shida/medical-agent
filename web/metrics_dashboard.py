"""
产品经理数据面板 - Web 可视化版本
基于 Streamlit 实现
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, timedelta
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.metrics import MetricsCollector
from utils.log_utils import setup_logger

setup_logger(level="INFO")

# 页面配置
st.set_page_config(
    page_title="产品经理数据面板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义 CSS
st.markdown(
    """
    <style>
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
        margin: 0.5rem 0;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1E88E5;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #666;
    }
    .success { color: #4CAF50; }
    .warning { color: #FF9800; }
    .error { color: #F44336; }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_metrics_data(collector: MetricsCollector, date: str = None):
    """获取指定日期的指标数据"""
    return collector.get_daily_metrics(date)


def get_trend_data(collector: MetricsCollector, days: int = 7):
    """获取趋势数据"""
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]
    dates.reverse()
    
    trend_data = []
    for date in dates:
        metrics = collector.get_daily_metrics(date)
        trend_data.append({
            "date": date,
            "llm_calls": metrics["llm"]["total_calls"],
            "llm_success_rate": metrics["llm"]["success_rate"],
            "rag_retrievals": metrics["rag"]["total_retrievals"],
            "rag_hit_rate": metrics["rag"]["hit_rate"],
            "intent_count": metrics["intent"]["total_classifications"],
            "intent_confidence": metrics["intent"]["avg_confidence"],
        })
    
    return trend_data


def render_metric_card(label, value, unit="", status="normal"):
    """渲染指标卡片"""
    status_class = {
        "success": "success",
        "warning": "warning",
        "error": "error",
        "normal": ""
    }.get(status, "")
    
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value {status_class}">{value}{unit}</div>
            <div class="metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    """主函数"""
    st.title("📊 产品经理数据面板")
    st.markdown("**实时监控产品关键指标，助力数据驱动决策**")
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 配置")
        
        # 日期选择
        selected_date = st.date_input(
            "选择日期",
            value=datetime.now(),
            key="date_selector"
        )
        
        # 趋势天数
        trend_days = st.slider(
            "趋势天数",
            min_value=1,
            max_value=30,
            value=7,
            key="trend_days"
        )
        
        st.divider()
        
        # 刷新按钮
        if st.button("🔄 刷新数据", key="refresh"):
            st.rerun()
        
        st.divider()
        
        # 数据说明
        st.header("📖 数据说明")
        st.markdown(
            """
            **数据来源**:
            - LLM 调用记录
            - RAG 检索记录
            - 意图识别记录
            - 用户会话记录
            
            **更新频率**: 实时
            
            **数据位置**: `data/metrics/`
            """
        )
    
    # 初始化收集器
    collector = MetricsCollector()
    
    # 获取数据
    date_str = selected_date.strftime("%Y-%m-%d")
    metrics = get_metrics_data(collector, date_str)
    trend_data = get_trend_data(collector, trend_days)
    
    # 主面板 - 今日概览
    st.header(f"📊 今日概览 - {date_str}")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        llm_success = metrics["llm"]["success_rate"]
        status = "success" if llm_success >= 95 else "warning" if llm_success >= 85 else "error"
        render_metric_card(
            "LLM 成功率",
            f"{llm_success:.1f}",
            "%",
            status
        )
    
    with col2:
        rag_hit = metrics["rag"]["hit_rate"]
        status = "success" if rag_hit >= 95 else "warning" if rag_hit >= 85 else "error"
        render_metric_card(
            "RAG 命中率",
            f"{rag_hit:.1f}",
            "%",
            status
        )
    
    with col3:
        intent_conf = metrics["intent"]["avg_confidence"] * 100
        status = "success" if intent_conf >= 90 else "warning" if intent_conf >= 80 else "error"
        render_metric_card(
            "意图准确率",
            f"{intent_conf:.1f}",
            "%",
            status
        )
    
    with col4:
        avg_time = metrics["llm"]["avg_response_time"]
        status = "success" if avg_time <= 3 else "warning" if avg_time <= 5 else "error"
        render_metric_card(
            "平均响应",
            f"{avg_time:.2f}",
            "秒",
            status
        )
    
    st.divider()
    
    # 详细指标
    st.header("📈 详细指标")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 LLM 调用")
        llm = metrics["llm"]
        st.metric("总调用次数", llm["total_calls"])
        st.metric("成功次数", llm["success_calls"])
        st.metric("失败次数", llm["failed_calls"])
        st.metric("总 Token 数", f"{llm['total_tokens']:,}")
        st.metric("平均响应时间", f"{llm['avg_response_time']:.2f}秒")
    
    with col2:
        st.subheader("📚 RAG 检索")
        rag = metrics["rag"]
        st.metric("总检索次数", rag["total_retrievals"])
        st.metric("成功次数", rag["success_retrievals"])
        st.metric("平均结果数", f"{rag['avg_results_count']:.1f}个")
        st.metric("平均响应时间", f"{rag['avg_response_time']:.2f}秒")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("🎯 意图识别")
        intent = metrics["intent"]
        st.metric("总识别次数", intent["total_classifications"])
        st.metric("平均置信度", f"{intent['avg_confidence']:.2f}")
        st.metric("高置信度比例", f"{intent['high_confidence_rate']:.1f}%")
        
        # 意图分布
        if intent["intent_distribution"]:
            st.write("**意图分布**:")
            for intent_type, count in sorted(
                intent["intent_distribution"].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                percentage = count / intent["total_classifications"] * 100 if intent["total_classifications"] > 0 else 0
                st.write(f"- {intent_type}: {count}次 ({percentage:.1f}%)")
    
    with col4:
        st.subheader("👥 用户指标")
        user = metrics["user"]
        st.metric("总会话数", user["total_sessions"])
        st.metric("独立用户数", user["unique_users"])
    
    st.divider()
    
    # 质量评估
    st.header("📊 质量评估")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        llm_success = metrics["llm"]["success_rate"]
        if llm_success >= 99:
            st.success(f"✅ LLM 成功率\n{llm_success:.1f}%")
        elif llm_success >= 95:
            st.info(f"⚠️ LLM 成功率\n{llm_success:.1f}%")
        else:
            st.error(f"❌ LLM 成功率\n{llm_success:.1f}%")
    
    with col2:
        rag_hit = metrics["rag"]["hit_rate"]
        if rag_hit >= 95:
            st.success(f"✅ RAG 命中率\n{rag_hit:.1f}%")
        elif rag_hit >= 85:
            st.info(f"⚠️ RAG 命中率\n{rag_hit:.1f}%")
        else:
            st.error(f"❌ RAG 命中率\n{rag_hit:.1f}%")
    
    with col3:
        intent_high = metrics["intent"]["high_confidence_rate"]
        if intent_high >= 90:
            st.success(f"✅ 意图准确率\n{intent_high:.1f}%")
        elif intent_high >= 80:
            st.info(f"⚠️ 意图准确率\n{intent_high:.1f}%")
        else:
            st.error(f"❌ 意图准确率\n{intent_high:.1f}%")
    
    with col4:
        avg_time = metrics["llm"]["avg_response_time"]
        if avg_time <= 3:
            st.success(f"✅ 响应时间\n{avg_time:.2f}秒")
        elif avg_time <= 5:
            st.info(f"⚠️ 响应时间\n{avg_time:.2f}秒")
        else:
            st.error(f"❌ 响应时间\n{avg_time:.2f}秒")
    
    st.divider()
    
    # 趋势图表
    st.header(f"📈 趋势分析（最近{trend_days}天）")
    
    # LLM 成功率趋势
    st.subheader("🤖 LLM 成功率趋势")
    llm_trend_data = {d["date"]: d["llm_success_rate"] for d in trend_data}
    st.line_chart(llm_trend_data)
    
    # RAG 命中率趋势
    st.subheader("📚 RAG 命中率趋势")
    rag_trend_data = {d["date"]: d["rag_hit_rate"] for d in trend_data}
    st.line_chart(rag_trend_data)
    
    # 调用量趋势
    st.subheader("📊 调用量趋势")
    call_trend_data = {
        "LLM 调用": {d["date"]: d["llm_calls"] for d in trend_data},
        "RAG 检索": {d["date"]: d["rag_retrievals"] for d in trend_data},
    }
    st.line_chart(call_trend_data)
    
    # 底部信息
    st.divider()
    st.markdown(
        """
        <div style="text-align: center; color: #666; padding: 1rem;">
            <p>💡 提示：数据实时更新，点击侧边栏刷新按钮获取最新数据</p>
            <p>📁 数据存储位置：<code>data/metrics/</code></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
