import React from 'react';

export const IntroSection: React.FC = () => {
  return (
    <div className="intro-section">
      <div className="intro-content">
        <h2>🤖 AI 트렌드 분석 어시스턴트</h2>
        <p className="intro-description">
          연구/기술/산업 등의 <strong>최신 트렌드</strong>를 분석하여 종합 보고서를 제공하는 AI 어시스턴트입니다.
        </p>
        <div className="intro-features">
          <div className="feature-item">
            <span className="feature-icon">🔍</span>
            <div>
              <h3>요구사항 명확화</h3>
              <p>대화를 통해 분석하고 싶은 주제와 범위를 명확히 파악합니다.</p>
            </div>
          </div>
          <div className="feature-item">
            <span className="feature-icon">📚</span>
            <div>
              <h3>자료 수집</h3>
              <p>웹 검색과 학술 논문 검색(ArXiv)을 통해 <strong>최신 정보</strong>를 수집합니다.</p>
            </div>
          </div>
          <div className="feature-item">
            <span className="feature-icon">✍️</span>
            <div>
              <h3>보고서 작성</h3>
              <p>수집된 자료를 바탕으로 테이블, 다이어그램, 출처가 포함된 마크다운 보고서를 생성합니다.</p>
            </div>
          </div>
        </div>
        <p className="intro-start">아래 입력창에 분석하고 싶은 주제를 입력해주세요.</p>
      </div>
    </div>
  );
};
