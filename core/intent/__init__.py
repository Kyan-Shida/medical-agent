"""
意图识别模块初始化
"""

from core.intent.classifier import IntentClassifier
from core.intent.router import IntentRouter

__all__ = [
    "IntentClassifier",
    "IntentRouter",
]
