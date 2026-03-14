/**
 * 聊天消息组件
 */

import React from 'react';
import { Message } from '../types';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6 animate-fade-in`}>
      <div className={`max-w-[80%] ${isUser ? 'order-1' : 'order-2'}`}>
        {/* 消息气泡 */}
        <div
          className={`px-6 py-4 ${
            isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'
          }`}
        >
          <Markdown remarkPlugins={[remarkGfm]}>{message.content}</Markdown>
        </div>

        {/* 意图信息（仅 AI 消息显示） */}
        {!isUser && message.intent && (
          <div className="mt-2 flex items-center gap-2">
            <IntentBadge
              type={message.intent.type}
              confidence={message.intent.confidence}
            />
            {message.intent.sub_category && (
              <span className="text-xs text-gray-500">
                · {message.intent.sub_category}
              </span>
            )}
          </div>
        )}

        {/* RAG 检索结果（仅 AI 消息显示） */}
        {!isUser && message.rag_results && message.rag_results.length > 0 && (
          <div className="mt-3">
            <details className="text-sm">
              <summary className="cursor-pointer text-blue-600 hover:text-blue-700 font-medium">
                📚 参考文档 ({message.rag_results.length})
              </summary>
              <div className="mt-2 space-y-2">
                {message.rag_results.map((doc, index) => (
                  <div
                    key={index}
                    className="bg-blue-50 border border-blue-100 rounded-lg p-3"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-blue-700">
                        文档 {index + 1}
                      </span>
                      <span className="text-xs text-blue-500">
                        相似度：{(doc.score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-gray-600 text-xs line-clamp-3">
                      {doc.content}
                    </p>
                  </div>
                ))}
              </div>
            </details>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * 意图标签组件
 */
interface IntentBadgeProps {
  type: string;
  confidence: number;
}

const IntentBadge: React.FC<IntentBadgeProps> = ({ type, confidence }) => {
  const intentConfig: Record<string, { label: string; icon: string; color: string }> = {
    medical: { label: '医疗问题', icon: '🩺', color: 'intent-medical' },
    chat: { label: '闲聊', icon: '💬', color: 'intent-chat' },
    unanswerable: { label: '无法回答', icon: '🚫', color: 'intent-unanswerable' },
    health_plan: { label: '健康计划', icon: '📋', color: 'intent-health-plan' },
  };

  const config = intentConfig[type] || { label: '未知', icon: '❓', color: '' };

  return (
    <div className={`intent-badge ${config.color}`}>
      <span className="mr-1">{config.icon}</span>
      <span>{config.label}</span>
      <span className="ml-2 opacity-75">({(confidence * 100).toFixed(0)}%)</span>
    </div>
  );
};

export default ChatMessage;
