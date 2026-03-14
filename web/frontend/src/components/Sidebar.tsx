/**
 * 侧边栏组件
 */

import React from 'react';

interface SidebarProps {
  onClearChat: () => void;
  messageCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({ onClearChat, messageCount }) => {
  return (
    <div className="w-72 bg-white border-r border-gray-200 h-full overflow-y-auto">
      <div className="p-6">
        {/* Logo 和标题 */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-blue-600 mb-2">
            🏥 医疗 Agent
          </h1>
          <p className="text-sm text-gray-600">
            基于 LLM + RAG + 意图识别
          </p>
        </div>

        {/* 系统状态 */}
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">系统状态</h2>
          <div className="space-y-2">
            <StatusItem label="LLM 服务" status="success" />
            <StatusItem label="RAG 检索" status="success" />
            <StatusItem label="意图识别" status="success" />
          </div>
        </div>

        {/* 对话统计 */}
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">对话统计</h2>
          <div className="bg-blue-50 rounded-lg p-4">
            <div className="text-2xl font-bold text-blue-600">
              {Math.ceil(messageCount / 2)}
            </div>
            <div className="text-sm text-gray-600">轮对话</div>
          </div>
        </div>

        {/* 快捷操作 */}
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">快捷操作</h2>
          <button
            onClick={onClearChat}
            className="w-full px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 transition-colors text-sm font-medium"
          >
            🗑️ 清空对话
          </button>
        </div>

        {/* 使用说明 */}
        <div>
          <h2 className="text-sm font-semibold text-gray-700 mb-3">使用说明</h2>
          <div className="text-xs text-gray-600 space-y-2">
            <p>1️⃣ 在下方输入您的问题</p>
            <p>2️⃣ 系统自动识别意图</p>
            <p>3️⃣ 获取专业医疗回答</p>
            <p>4️⃣ 查看参考文档</p>
          </div>
        </div>
      </div>
    </div>
  );
};

interface StatusItemProps {
  label: string;
  status: 'success' | 'warning' | 'error';
}

const StatusItem: React.FC<StatusItemProps> = ({ label, status }) => {
  const statusConfig = {
    success: { color: 'text-green-600', bg: 'bg-green-100', icon: '✅' },
    warning: { color: 'text-orange-600', bg: 'bg-orange-100', icon: '⚠️' },
    error: { color: 'text-red-600', bg: 'bg-red-100', icon: '❌' },
  };

  const config = statusConfig[status];

  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-gray-600">{label}</span>
      <span className={`px-2 py-1 rounded ${config.bg} ${config.color}`}>
        {config.icon}
      </span>
    </div>
  );
};

export default Sidebar;
