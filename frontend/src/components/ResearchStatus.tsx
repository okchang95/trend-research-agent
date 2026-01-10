import React from 'react';
import { SearchResult } from '../types';

interface ResearchStatusProps {
  message: string;
  results?: SearchResult[];
}

export const ResearchStatus: React.FC<ResearchStatusProps> = ({ message, results }) => {
  return (
    <div className="research-status-container">
      <div className="research-status-message">{message}</div>
      {results && results.length > 0 && (
        <div className="research-results-preview">
          {results.map((result, index) => (
            <div key={index} className="result-preview-item">
              {result.url ? (
                <a
                  href={result.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="result-preview-link"
                >
                  {result.title || '제목 없음'}
                </a>
              ) : (
                <span className="result-preview-title">{result.title || '제목 없음'}</span>
              )}
              {result.snippet && (
                <div className="result-preview-snippet">{result.snippet}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
