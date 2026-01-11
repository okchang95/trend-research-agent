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
  scrollTrigger?: number; // 메시지 전송 시 증가하는 트리거
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  streamingContent,
  isStreaming = false,
  nodeStatus = null,
  researchStatus = null,
  findings = [],
  scrollTrigger = 0,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamingMessageRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const lastUserMessageRef = useRef<HTMLDivElement>(null);

  // 메시지 전송 시에만 마지막 사용자 메시지가 화면 상단에 오도록 스크롤
  useEffect(() => {
    if (scrollTrigger > 0 && lastUserMessageRef.current && messagesContainerRef.current) {
      // 약간의 지연을 두어 렌더링 완료 후 스크롤
      setTimeout(() => {
        lastUserMessageRef.current?.scrollIntoView({ 
          behavior: 'smooth',
          block: 'start'  // 화면 상단에 위치
        });
      }, 100);
    }
  }, [scrollTrigger]);

  // 스트리밍 메시지의 마크다운 렌더링
  useEffect(() => {
    if (isStreaming && streamingMessageRef.current && streamingContent) {
      renderMermaidDiagrams(streamingMessageRef.current);
    }
  }, [streamingContent, isStreaming]);

  const renderStreamingContent = () => {
    // 중간 상태가 하나라도 있으면 그것들을 표시
    const hasIntermediateStatus = nodeStatus || researchStatus || findings.length > 0;
    
    if (!streamingContent && !hasIntermediateStatus) {
      return <div className="thinking-indicator">생각중...</div>;
    }
    
    return (
      <>
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
        {streamingContent && (
          <div dangerouslySetInnerHTML={{ __html: processMarkdownWithMermaid(streamingContent) }} />
        )}
      </>
    );
  };

  // 마지막 user 메시지 인덱스 찾기
  const lastUserMessageIndex = messages.reduce((lastIndex, msg, index) => {
    return msg.role === 'user' ? index : lastIndex;
  }, -1);

  return (
    <div className="messages-container" ref={messagesContainerRef}>
      {messages.map((msg, index) => {
        const isLastUserMessage = msg.role === 'user' && index === lastUserMessageIndex;
        
        return (
          <div 
            key={index}
            ref={isLastUserMessage ? lastUserMessageRef : undefined}
          >
            <Message role={msg.role} content={msg.message} />
            {/* writer 노드에서 종료된 메시지에만 findings를 별도 블록으로 표시 */}
            {msg.role === 'assistant' && msg.ended_node === 'writer' && msg.findings && msg.findings.length > 0 && (
              <div className="message assistant-message">
                <div className="message-content">
                  <div className="message-text">
                    <ResearchFindings findings={msg.findings} />
                  </div>
                </div>
              </div>
            )}
          </div>
        );
      })}
      {isStreaming && (
        <div className="message assistant-message">
          <div className="message-content">
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
