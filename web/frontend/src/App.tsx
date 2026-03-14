/**
 * 主应用组件
 */

import React, { useState, useRef, useEffect } from 'react';
import { sendChat } from './api/client';
import { Message, QuickTag, ChatResponse, LoadingState as LoadingStateType } from './types';
import ChatMessage from './components/ChatMessage';
import LoadingState from './components/LoadingState';
import ChatInput from './components/ChatInput';
import QuickTags from './components/QuickTags';
import Disclaimer from './components/Disclaimer';
import Sidebar from './components/Sidebar';

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingState, setLoadingState] = useState<LoadingStateType>({
    analyzing: false,
    retrieving: false,
    generating: false,
    step: '',
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 快捷标签
  const quickTags: QuickTag[] = [
    { label: '儿童发烧', value: '孩子发烧了怎么办？', icon: '🤒' },
    { label: '制定计划', value: '帮我制定健康计划', icon: '📋' },
    { label: '感冒症状', value: '感冒了有哪些症状？', icon: '🤧' },
    { label: '饮食建议', value: '有什么饮食建议吗？', icon: '🥗' },
  ];

  // 自动滚动到底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 发送消息
  const handleSend = async (content: string) => {
    // 添加用户消息
    const userMessage: Message = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // 设置加载状态
    setIsLoading(true);
    setLoadingState({
      analyzing: true,
      retrieving: false,
      generating: false,
      step: '正在分析您的意图...',
    });

    try {
      // 模拟加载步骤（更好的用户体验）
      setTimeout(() => {
        setLoadingState((prev) => ({
          ...prev,
          retrieving: true,
          step: '正在检索权威医学库...',
        }));
      }, 800);

      setTimeout(() => {
        setLoadingState((prev) => ({
          ...prev,
          generating: true,
          step: '正在综合专家意见...',
        }));
      }, 1600);

      // 发送 API 请求
      const response = await sendChat({ message: content });

      if (response.success && response.message) {
        setMessages((prev) => [...prev, response.message!]);
      } else {
        // 错误消息
        const errorMessage: Message = {
          role: 'assistant',
          content: `❌ 处理失败：${response.error || '未知错误'}`,
          timestamp: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      // 错误处理
      const errorMessage: Message = {
        role: 'assistant',
        content: `❌ 请求失败：${error instanceof Error ? error.message : '未知错误'}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setLoadingState({
        analyzing: false,
        retrieving: false,
        generating: false,
        step: '',
      });
    }
  };

  // 选择快捷标签
  const handleSelectTag = (tag: QuickTag) => {
    handleSend(tag.value);
  };

  // 清空对话
  const handleClearChat = () => {
    setMessages([]);
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-blue-50 to-gray-100">
      {/* 侧边栏 */}
      <Sidebar onClearChat={handleClearChat} messageCount={messages.length} />

      {/* 主聊天区域 */}
      <div className="flex-1 flex flex-col">
        {/* 顶部标题栏 */}
        <header className="bg-white border-b border-gray-200 px-8 py-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-blue-600">
                🏥 医疗智能助手
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                专业、可靠、贴心的医疗咨询服务
              </p>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-xs text-gray-500">
                已对话 {Math.ceil(messages.length / 2)} 轮
              </span>
            </div>
          </div>
        </header>

        {/* 消息列表 */}
        <main className="flex-1 overflow-y-auto px-8 py-6">
          <div className="max-w-4xl mx-auto">
            {/* 欢迎消息 */}
            {messages.length === 0 && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🏥</div>
                <h2 className="text-2xl font-bold text-gray-700 mb-2">
                  您好，我是您的医疗智能助手
                </h2>
                <p className="text-gray-600 mb-8">
                  基于权威医学知识库，为您提供专业的健康咨询服务
                </p>
                <div className="text-sm text-gray-500">
                  <p>💡 试试问我：</p>
                  <QuickTags tags={quickTags} onSelect={handleSelectTag} disabled={false} />
                </div>
              </div>
            )}

            {/* 历史消息 */}
            {messages.map((message, index) => (
              <ChatMessage key={index} message={message} />
            ))}

            {/* 加载状态 */}
            {isLoading && (
              <LoadingState
                analyzing={loadingState.analyzing}
                retrieving={loadingState.retrieving}
                generating={loadingState.generating}
                step={loadingState.step}
              />
            )}

            {/* 滚动锚点 */}
            <div ref={messagesEndRef} />
          </div>
        </main>

        {/* 底部输入区域 */}
        <footer className="bg-white border-t border-gray-200 px-8 py-6">
          <div className="max-w-4xl mx-auto">
            {/* 快捷标签 */}
            <div className="mb-4">
              <QuickTags tags={quickTags} onSelect={handleSelectTag} disabled={isLoading} />
            </div>

            {/* 输入框 */}
            <div className="mb-4">
              <ChatInput onSend={handleSend} disabled={isLoading} />
            </div>

            {/* 免责声明 */}
            <Disclaimer />

            {/* 底部信息 */}
            <div className="mt-4 text-center text-xs text-gray-500">
              <p>Powered by LLM + RAG + Intent Recognition</p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default App;
