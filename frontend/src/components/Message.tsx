import React, { useEffect, useRef } from 'react';
import { processMarkdownWithMermaid, renderMermaidDiagrams } from '../utils/markdown';

interface MessageProps {
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
}

export const Message: React.FC<MessageProps> = ({ role, content, isStreaming = false }) => {
  const messageRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (role === 'assistant' && messageRef.current) {
      renderMermaidDiagrams(messageRef.current);
    }
  }, [content, role]);

  const renderContent = () => {
    if (role === 'user') {
      return <div className="message-text">{content}</div>;
    }

    // Assistant 메시지는 마크다운 처리
    const html = processMarkdownWithMermaid(content);
    return (
      <div
        className="message-text"
        ref={messageRef}
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  };

  return (
    <div className={`message ${role}-message`}>
      <div className="message-content">
        {renderContent()}
        {isStreaming && role === 'assistant' && content === '' && (
          <div className="thinking-indicator">생각중...</div>
        )}
      </div>
    </div>
  );
};
