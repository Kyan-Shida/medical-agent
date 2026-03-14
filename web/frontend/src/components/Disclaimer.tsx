/**
 * 免责声明组件
 */

import React from 'react';

export const Disclaimer: React.FC = () => {
  return (
    <div className="disclaimer mt-4">
      <div className="flex items-start gap-3">
        <span className="text-lg">⚠️</span>
        <div>
          <p className="font-medium mb-1">医疗免责声明</p>
          <p className="text-sm leading-relaxed">
            本 AI 助手提供的信息仅供参考，不能替代专业医疗建议、诊断或治疗。
            如有健康问题，请咨询医生或其他合格的医疗专业人员。
            如有紧急情况，请立即拨打急救电话或前往最近的急诊室。
          </p>
        </div>
      </div>
    </div>
  );
};

export default Disclaimer;
