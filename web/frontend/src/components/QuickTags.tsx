/**
 * 快捷标签组件
 */

import React from 'react';
import { QuickTag } from '../types';

interface QuickTagsProps {
  tags: QuickTag[];
  onSelect: (tag: QuickTag) => void;
  disabled?: boolean;
}

export const QuickTags: React.FC<QuickTagsProps> = ({ tags, onSelect, disabled }) => {
  return (
    <div className="flex flex-wrap gap-2">
      {tags.map((tag, index) => (
        <button
          key={index}
          onClick={() => onSelect(tag)}
          disabled={disabled}
          className="px-4 py-2 bg-white border-2 border-blue-100 rounded-full text-sm text-blue-700 hover:bg-blue-50 hover:border-blue-300 focus:outline-none focus:ring-2 focus:ring-blue-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105 active:scale-95 flex items-center gap-2"
        >
          {tag.icon && <span>{tag.icon}</span>}
          {tag.label}
        </button>
      ))}
    </div>
  );
};

export default QuickTags;
