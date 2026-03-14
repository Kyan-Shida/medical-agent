/**
 * 加载状态组件
 */

import React from 'react';
import { motion } from 'framer-motion';

interface LoadingStateProps {
  analyzing: boolean;
  retrieving: boolean;
  generating: boolean;
  step: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  analyzing,
  retrieving,
  generating,
  step,
}) => {
  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-[80%]">
        <div className="chat-bubble-assistant px-6 py-4">
          {/* 加载动画 */}
          <div className="flex items-center space-x-2">
            <div className="loading-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span className="text-gray-600 text-sm">{step}</span>
          </div>

          {/* 进度步骤 */}
          <div className="mt-4 space-y-2">
            <StepIndicator
              active={analyzing}
              completed={retrieving || generating}
              label="正在分析意图"
              icon="🎯"
            />
            <StepIndicator
              active={retrieving}
              completed={generating}
              label="正在检索医学知识库"
              icon="📚"
            />
            <StepIndicator
              active={generating}
              completed={false}
              label="正在生成专业回答"
              icon="✍️"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

interface StepIndicatorProps {
  active: boolean;
  completed: boolean;
  label: string;
  icon: string;
}

const StepIndicator: React.FC<StepIndicatorProps> = ({
  active,
  completed,
  label,
  icon,
}) => {
  return (
    <motion.div
      className={`flex items-center space-x-2 text-sm ${
        completed ? 'text-green-600' : active ? 'text-blue-600' : 'text-gray-400'
      }`}
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
    >
      <span className="text-base">{icon}</span>
      <span>{label}</span>
      {active && (
        <motion.span
          className="loading-dots"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <span></span>
          <span></span>
          <span></span>
        </motion.span>
      )}
      {completed && <span>✅</span>}
    </motion.div>
  );
};

export default LoadingState;
