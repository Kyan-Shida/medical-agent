/**
 * @fileoverview 类型定义
 */

// 意图类型
export type IntentType = 'medical' | 'chat' | 'unanswerable' | 'health_plan';

// 意图信息
export interface Intent {
  type: IntentType;
  confidence: number;
  sub_category?: string;
}

// RAG 检索结果
export interface RagResult {
  content: string;
  score: number;
}

// 消息
export interface Message {
  role: 'user' | 'assistant';
  content: string;
  intent?: Intent;
  rag_results?: RagResult[];
  timestamp?: string;
}

// 聊天请求
export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

// 聊天响应
export interface ChatResponse {
  success: boolean;
  message?: Message;
  intent?: Intent;
  rag_results?: RagResult[];
  metadata?: {
    response_length: number;
    processing_time: number;
  };
  error?: string;
}

// 快捷标签
export interface QuickTag {
  label: string;
  value: string;
  icon?: string;
}

// 加载状态
export interface LoadingState {
  analyzing: boolean;
  retrieving: boolean;
  generating: boolean;
  step: string;
}
