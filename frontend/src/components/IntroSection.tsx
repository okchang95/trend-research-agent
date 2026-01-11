import React from 'react';

interface IntroSectionProps {
  onExampleClick?: (example: string) => void;
}

export const IntroSection: React.FC<IntroSectionProps> = ({ onExampleClick }) => {
  const examples = [
    {
      icon: '🤖',
      title: 'AI 에이전트 시장',
      query: '2026년 AI 에이전트 시장 전망과 주요 트렌드',
      description: '시장 규모, 주요 기업, 기술 동향'
    },
    {
      icon: '🧬',
      title: '바이오 기술',
      query: '최근 mRNA 백신 기술 발전 동향',
      description: '연구 현황, 신약 개발 트렌드'
    },
    {
      icon: '⚡',
      title: '에너지 기술',
      query: '고체 배터리 기술의 최신 연구 동향',
      description: '기술 혁신, 상용화 전망'
    },
    {
      icon: '🌐',
      title: '웹 기술',
      query: '2025-2026 프론트엔드 개발 트렌드',
      description: '프레임워크, 도구, 패러다임 변화'
    }
  ];

  return (
    <div className="intro-section">
      <div className="intro-content">
        <h2>🤖 AI 트렌드 분석 어시스턴트</h2>
        <p className="intro-description">
          연구/기술/산업 등의 <strong>최신 트렌드</strong>를 분석하여 종합 보고서를 제공하는 AI 어시스턴트입니다.
        </p>
        
        <div className="how-to-use">
          <h3>💡 이렇게 질문해보세요</h3>
          <p className="how-to-description">
            분석하고 싶은 <strong>주제</strong>와 <strong>시기</strong>를 함께 입력하면 더 정확한 보고서를 받을 수 있습니다.
          </p>
        </div>

        <div className="example-cards">
          {examples.map((example, index) => (
            <div 
              key={index}
              className="example-card"
              onClick={() => onExampleClick?.(example.query)}
            >
              <div className="example-icon">{example.icon}</div>
              <div className="example-content">
                <h4>{example.title}</h4>
                <p className="example-query">"{example.query}"</p>
                <p className="example-description">{example.description}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="intro-features-compact">
          <span className="feature-badge">🔍 요구사항 명확화</span>
          <span className="feature-badge">📚 웹 & 논문 검색</span>
          <span className="feature-badge">✍️ 보고서 작성</span>
        </div>
      </div>
    </div>
  );
};
