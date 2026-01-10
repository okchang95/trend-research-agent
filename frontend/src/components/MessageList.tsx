import React, { useEffect, useRef } from 'react';
import { Message } from './Message';
import { NodeStatus } from './NodeStatus';
import { ResearchStatus } from './ResearchStatus';
import { ResearchFindings } from './ResearchFindings';
import { Message as MessageType, SearchResult, Finding } from '../types';
import { processMarkdownWithMermaid, renderMermaidDiagrams } from '../utils/markdown';

interface MessageListProps {
  messages: MessageType[];
  streamingContent?: string;
  isStreaming?: boolean;
  nodeStatus?: { name: string; status: 'in_progress' | 'completed' } | null;
  researchStatus?: { message: string; results?: SearchResult[] } | null;
  findings?: Finding[];
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  streamingContent,
  isStreaming = false,
  nodeStatus = null,
  researchStatus = null,
  findings = [],
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamingMessageRef = useRef<HTMLDivElement>(null);

  // 새 메시지가 추가되면 스크롤을 맨 아래로
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingContent, nodeStatus, researchStatus, findings]);

  // 스트리밍 메시지의 마크다운 렌더링
  useEffect(() => {
    if (isStreaming && streamingMessageRef.current && streamingContent) {
      renderMermaidDiagrams(streamingMessageRef.current);
    }
  }, [streamingContent, isStreaming]);

  const renderStreamingContent = () => {
    if (!streamingContent) {
      return <div className="thinking-indicator">생각중...</div>;
    }
    const html = processMarkdownWithMermaid(streamingContent);
    return <div dangerouslySetInnerHTML={{ __html: html }} />;
  };

  return (
    <div className="messages-container">
      {messages.map((msg, index) => (
        <Message key={index} role={msg.role} content={msg.message} />
      ))}
      {isStreaming && (
        <div className="message assistant-message">
          <div className="message-content">
            {nodeStatus && (
              <NodeStatus nodeName={nodeStatus.name} status={nodeStatus.status} />
            )}
            {researchStatus && (
              <ResearchStatus
                message={researchStatus.message}
                results={researchStatus.results}
              />
            )}
            {findings.length > 0 && <ResearchFindings findings={findings} />}
            <div className="message-text" ref={streamingMessageRef}>
              {renderStreamingContent()}
            </div>
          </div>
        </div>
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};
