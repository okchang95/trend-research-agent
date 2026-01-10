import React, { useState } from 'react';
import { Finding } from '../types';

interface ResearchFindingsProps {
  findings: Finding[];
}

export const ResearchFindings: React.FC<ResearchFindingsProps> = ({ findings }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!findings || findings.length === 0) return null;

  // findings 데이터 검증 및 필터링
  const validFindings = findings.filter((finding) => {
    if (!finding || typeof finding !== 'object') return false;
    return true;
  });

  if (validFindings.length === 0) return null;

  return (
    <div className="research-findings-container">
      <div className="research-findings-header">
        <button
          className="research-findings-toggle"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <span className="toggle-icon">{isExpanded ? '▲' : '▼'}</span>{' '}
          <span className="toggle-text">
            {isExpanded ? '조사 내용 숨기기' : '조사 내용 보기'}
          </span>{' '}
          <span className="findings-count">({validFindings.length}개)</span>
        </button>
      </div>
      {isExpanded && (
        <div className="research-findings-content">
          {validFindings.map((finding, index) => {
            try {
              if (finding.type === 'final_summary') {
                return (
                  <div key={index} className="finding-item finding-summary">
                    <div className="finding-header">📝 최종 요약</div>
                    <div className="finding-content">{finding.summary || ''}</div>
                  </div>
                );
              }

              // results가 배열인지 확인
              const results = Array.isArray(finding.results) ? finding.results : [];

              return (
                <div key={index} className="finding-item">
                  <div className="finding-header">
                    <span className="finding-number">{finding.iteration || index + 1}</span>
                    <span className="finding-query">{finding.query || '쿼리 없음'}</span>
                    <span className="finding-tool-type">
                      {finding.tool_type === 'web_search' ? '🌐' : '📄'}
                    </span>
                  </div>
                  <div className="finding-content">
                    {results.length > 0 ? (
                      results.map((result, rIndex) => {
                        if (!result || typeof result !== 'object') {
                          return null;
                        }

                        const contentPreview =
                          result.content && typeof result.content === 'string' && result.content.length > 200
                            ? result.content.substring(0, 200) + '...'
                            : result.content || '';

                        return (
                          <div key={rIndex} className="finding-result">
                            <div className="result-title">{result.title || '제목 없음'}</div>
                            {result.url && (
                              <div className="result-url">
                                <a
                                  href={result.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  {result.url}
                                </a>
                              </div>
                            )}
                            {contentPreview && (
                              <div className="result-content">{contentPreview}</div>
                            )}
                          </div>
                        );
                      })
                    ) : (
                      <div className="finding-result">결과 없음</div>
                    )}
                  </div>
                </div>
              );
            } catch (error) {
              console.error('Finding render error:', error, finding);
              return null;
            }
          })}
        </div>
      )}
    </div>
  );
};
