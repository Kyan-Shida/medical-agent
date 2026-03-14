/**
 * API 客户端
 */

import axios from 'axios';
import { ChatRequest, ChatResponse } from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 发送聊天消息
 */
export const sendChat = async (request: ChatRequest): Promise<ChatResponse> => {
  try {
    const response = await api.post<ChatResponse>('/api/chat', request);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      throw new Error(error.response?.data?.detail || '网络请求失败');
    }
    throw error;
  }
};

/**
 * 健康检查
 */
export const healthCheck = async (): Promise<{
  status: string;
  llm: boolean;
  rag: boolean;
  intent_classifier: boolean;
}> => {
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error) {
    throw new Error('API 服务不可用');
  }
};

export default api;
