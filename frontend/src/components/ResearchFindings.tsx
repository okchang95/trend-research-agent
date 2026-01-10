import React, { useState } from 'react';
import { Finding } from '../types';

interface ResearchFindingsProps {
  findings: Finding[];
}

export const ResearchFindings: React.FC<ResearchFindingsProps> = ({ findings }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!findings || findings.length === 0) return null;

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
          <span className="findings-count">({findings.length}개)</span>
        </button>
      </div>
      {isExpanded && (
        <div className="research-findings-content">
          {findings.map((finding, index) => {
            if (finding.type === 'final_summary') {
              return (
                <div key={index} className="finding-item finding-summary">
                  <div className="finding-header">📝 최종 요약</div>
                  <div className="finding-content">{finding.summary}</div>
                </div>
              );
            }

            return (
              <div key={index} className="finding-item">
                <div className="finding-header">
                  <span className="finding-number">{finding.iteration || index + 1}</span>
                  <span className="finding-query">{finding.query || ''}</span>
                  <span className="finding-tool-type">
                    {finding.tool_type === 'web_search' ? '🌐' : '📄'}
                  </span>
                </div>
                <div className="finding-content">
                  {finding.results && finding.results.length > 0 ? (
                    finding.results.map((result, rIndex) => {
                      const contentPreview =
                        result.content && result.content.length > 200
                          ? result.content.substring(0, 200) + '...'
                          : result.content;

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
          })}
        </div>
      )}
    </div>
  );
};
