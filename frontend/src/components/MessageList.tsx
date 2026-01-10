import React, { useEffect, useRef, useState } from 'react';
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
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

  // 사용자가 스크롤 위치를 변경했는지 감지 (window 스크롤 감지)
  const handleScroll = () => {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollHeight = document.documentElement.scrollHeight;
    const clientHeight = window.innerHeight;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    
    // 하단에서 30px 이내면 자동 스크롤 활성화, 그렇지 않으면 비활성화
    setShouldAutoScroll(distanceFromBottom < 30);
  };

  // 스크롤 이벤트 리스너 등록 (window 레벨)
  useEffect(() => {
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 새 메시지가 추가되면 스크롤을 맨 아래로 (사용자가 하단에 있을 때만)
  useEffect(() => {
    if (shouldAutoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingContent, nodeStatus, researchStatus, findings, shouldAutoScroll]);

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
