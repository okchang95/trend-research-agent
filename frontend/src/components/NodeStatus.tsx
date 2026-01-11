import React from 'react';

interface NodeStatusProps {
  nodeName: string;
  status: 'in_progress' | 'completed';
}

export const NodeStatus: React.FC<NodeStatusProps> = ({ nodeName, status }) => {
  const getNodeInfo = (name: string, isCompleted: boolean) => {
    if (!isCompleted) {
      switch (name) {
        case 'clarify_requirement':
          return { icon: '🔍', text: '요구사항 명확화 중...' };
        case 'researcher':
          return { icon: '📚', text: '자료 수집 중...' };
        case 'writer':
          return { icon: '✍️', text: '보고서 작성 중...' };
        case 'generating':
          return { icon: '⚙️', text: '응답 생성 중...' };
        default:
          return { icon: '⏳', text: `${name} 진행 중...` };
      }
    } else {
      switch (name) {
        case 'clarify_requirement':
          return { icon: '✅', text: '명확화 완료' };
        case 'researcher':
          return null; // researcher 완료는 표시하지 않음
        case 'writer':
          return { icon: '✅', text: '작성 완료' };
        default:
          return { icon: '✅', text: `${name} 완료` };
      }
    }
  };

  const nodeInfo = getNodeInfo(nodeName, status === 'completed');
  
  if (!nodeInfo) return null;

  return (
    <div className={`node-status ${status === 'in_progress' ? 'progressing' : ''}`}>
      <div className="loading">
        {nodeInfo.icon} {nodeInfo.text}
      </div>
    </div>
  );
};
