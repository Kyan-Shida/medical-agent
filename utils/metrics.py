"""
产品数据指标收集模块
收集用户行为、性能指标、业务数据
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from utils.log_utils import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """产品指标收集器"""

    def __init__(self, data_dir: str = "data/metrics"):
        """
        初始化指标收集器

        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)

        # 初始化指标缓存
        self.metrics_cache = {
            "llm_calls": [],  # LLM 调用记录
            "rag_retrievals": [],  # RAG 检索记录
            "intent_classifications": [],  # 意图识别记录
            "user_sessions": [],  # 用户会话记录
        }

    def record_llm_call(
        self,
        success: bool,
        tokens_used: int,
        response_time: float,
        model: str = "glm-4-flash",
        error: Optional[str] = None,
    ):
        """
        记录 LLM 调用

        Args:
            success: 是否成功
            tokens_used: 使用的 token 数
            response_time: 响应时间（秒）
            model: 模型名称
            error: 错误信息（如果失败）
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "type": "llm_call",
            "success": success,
            "tokens_used": tokens_used,
            "response_time": response_time,
            "model": model,
            "error": error,
        }

        self.metrics_cache["llm_calls"].append(record)
        self.logger.debug(f"记录 LLM 调用：success={success}, time={response_time:.2f}s")

    def record_rag_retrieval(
        self,
        success: bool,
        results_count: int,
        response_time: float,
        query: str = "",
    ):
        """
        记录 RAG 检索

        Args:
            success: 是否成功
            results_count: 检索结果数
            response_time: 响应时间（秒）
            query: 查询内容
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "type": "rag_retrieval",
            "success": success,
            "results_count": results_count,
            "response_time": response_time,
            "query_preview": query[:50] if query else "",
        }

        self.metrics_cache["rag_retrievals"].append(record)
        self.logger.debug(f"记录 RAG 检索：success={success}, count={results_count}")

    def record_intent_classification(
        self,
        intent: str,
        confidence: float,
        sub_category: Optional[str] = None,
        response_time: float = 0,
    ):
        """
        记录意图识别

        Args:
            intent: 意图类型
            confidence: 置信度
            sub_category: 子分类
            response_time: 响应时间（秒）
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "type": "intent_classification",
            "intent": intent,
            "confidence": confidence,
            "sub_category": sub_category,
            "response_time": response_time,
        }

        self.metrics_cache["intent_classifications"].append(record)
        self.logger.debug(f"记录意图识别：intent={intent}, confidence={confidence:.2f}")

    def record_user_session(
        self,
        user_id: str,
        session_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        记录用户会话

        Args:
            user_id: 用户 ID
            session_id: 会话 ID
            action: 操作类型
            details: 详细信息
        """
        record = {
            "timestamp": datetime.now().isoformat(),
            "type": "user_session",
            "user_id": user_id,
            "session_id": session_id,
            "action": action,
            "details": details or {},
        }

        self.metrics_cache["user_sessions"].append(record)

    def save_metrics(self, date: Optional[str] = None):
        """
        保存指标到文件

        Args:
            date: 日期（YYYY-MM-DD 格式，默认为今天）
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        # 按类型保存指标
        for metric_type, records in self.metrics_cache.items():
            if not records:
                continue

            # 保存到文件
            filename = self.data_dir / f"{metric_type}_{date}.json"

            # 如果文件存在，追加数据
            existing_data = []
            if filename.exists():
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                except:
                    pass

            # 合并数据
            existing_data.extend(records)

            # 保存
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"保存 {len(records)} 条 {metric_type} 记录到 {filename}")

            # 清空缓存
            self.metrics_cache[metric_type] = []

    def get_daily_metrics(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取每日指标汇总

        Args:
            date: 日期（默认为今天）

        Returns:
            指标汇总字典
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        metrics = {
            "date": date,
            "llm": {
                "total_calls": 0,
                "success_calls": 0,
                "failed_calls": 0,
                "success_rate": 0,
                "total_tokens": 0,
                "avg_response_time": 0,
            },
            "rag": {
                "total_retrievals": 0,
                "success_retrievals": 0,
                "hit_rate": 0,
                "avg_results_count": 0,
                "avg_response_time": 0,
            },
            "intent": {
                "total_classifications": 0,
                "intent_distribution": {},
                "avg_confidence": 0,
                "high_confidence_rate": 0,
            },
            "user": {
                "total_sessions": 0,
                "unique_users": 0,
            },
        }

        # 计算 LLM 指标
        llm_file = self.data_dir / f"llm_calls_{date}.json"
        if llm_file.exists():
            with open(llm_file, "r", encoding="utf-8") as f:
                llm_records = json.load(f)

            metrics["llm"]["total_calls"] = len(llm_records)
            metrics["llm"]["success_calls"] = sum(
                1 for r in llm_records if r.get("success", False)
            )
            metrics["llm"]["failed_calls"] = (
                metrics["llm"]["total_calls"] - metrics["llm"]["success_calls"]
            )

            if metrics["llm"]["total_calls"] > 0:
                metrics["llm"]["success_rate"] = (
                    metrics["llm"]["success_calls"] / metrics["llm"]["total_calls"] * 100
                )

            metrics["llm"]["total_tokens"] = sum(
                r.get("tokens_used", 0) for r in llm_records
            )

            response_times = [r.get("response_time", 0) for r in llm_records]
            if response_times:
                metrics["llm"]["avg_response_time"] = sum(response_times) / len(
                    response_times
                )

        # 计算 RAG 指标
        rag_file = self.data_dir / f"rag_retrievals_{date}.json"
        if rag_file.exists():
            with open(rag_file, "r", encoding="utf-8") as f:
                rag_records = json.load(f)

            metrics["rag"]["total_retrievals"] = len(rag_records)
            metrics["rag"]["success_retrievals"] = sum(
                1 for r in rag_records if r.get("success", False)
            )

            if metrics["rag"]["total_retrievals"] > 0:
                metrics["rag"]["hit_rate"] = (
                    metrics["rag"]["success_retrievals"]
                    / metrics["rag"]["total_retrievals"]
                    * 100
                )

                results_counts = [r.get("results_count", 0) for r in rag_records]
                if results_counts:
                    metrics["rag"]["avg_results_count"] = sum(results_counts) / len(
                        results_counts
                    )

                response_times = [r.get("response_time", 0) for r in rag_records]
                if response_times:
                    metrics["rag"]["avg_response_time"] = sum(response_times) / len(
                        response_times
                    )

        # 计算意图识别指标
        intent_file = self.data_dir / f"intent_classifications_{date}.json"
        if intent_file.exists():
            with open(intent_file, "r", encoding="utf-8") as f:
                intent_records = json.load(f)

            metrics["intent"]["total_classifications"] = len(intent_records)

            # 意图分布
            intent_counts = {}
            for record in intent_records:
                intent = record.get("intent", "unknown")
                intent_counts[intent] = intent_counts.get(intent, 0) + 1

            metrics["intent"]["intent_distribution"] = intent_counts

            # 平均置信度
            confidences = [r.get("confidence", 0) for r in intent_records]
            if confidences:
                metrics["intent"]["avg_confidence"] = sum(confidences) / len(confidences)

                # 高置信度比例（>0.8）
                high_confidence = sum(1 for c in confidences if c > 0.8)
                metrics["intent"]["high_confidence_rate"] = (
                    high_confidence / len(confidences) * 100
                )

        # 用户指标
        user_file = self.data_dir / f"user_sessions_{date}.json"
        if user_file.exists():
            with open(user_file, "r", encoding="utf-8") as f:
                user_records = json.load(f)

            metrics["user"]["total_sessions"] = len(user_records)
            unique_users = set(r.get("user_id") for r in user_records)
            metrics["user"]["unique_users"] = len(unique_users)

        return metrics


# 全局指标收集器实例
collector = MetricsCollector()


def get_collector() -> MetricsCollector:
    """获取指标收集器实例"""
    return collector
