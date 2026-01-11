import React, { useEffect, useRef, useState, useCallback } from 'react';
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
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [shouldAutoScroll, setShouldAutoScroll] = useState(true);

  // 메시지 컨테이너의 스크롤 위치 감지
  const handleScroll = useCallback(() => {
    if (!messagesContainerRef.current) return;
    
    const container = messagesContainerRef.current;
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    
    // 하단에서 100px 이상 떨어지면 자동 스크롤 비활성화
    // 50px 이내면 자동 스크롤 활성화
    setShouldAutoScroll(distanceFromBottom < 50);
  }, []);

  // 스크롤 이벤트 리스너 등록
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;
    
    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => container.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  // 새 메시지가 추가되면 스크롤을 맨 아래로 (자동 스크롤이 활성화된 경우만)
  useEffect(() => {
    if (shouldAutoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingContent, shouldAutoScroll]);

  // 키보드가 열릴 때 스크롤을 하단으로 유지
  useEffect(() => {
    const handleResize = () => {
      // 키보드가 열리거나 닫힐 때 (viewport height 변경)
      if (shouldAutoScroll && messagesEndRef.current) {
        // 약간의 지연을 두어 레이아웃이 완료된 후 스크롤
        setTimeout(() => {
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
        }, 100);
      }
    };

    window.addEventListener('resize', handleResize);
    // visualViewport API 사용 (모바일 키보드 감지)
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', handleResize);
    }

    return () => {
      window.removeEventListener('resize', handleResize);
      if (window.visualViewport) {
        window.visualViewport.removeEventListener('resize', handleResize);
      }
    };
  }, [shouldAutoScroll]);

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

  return (
    <div className="messages-container" ref={messagesContainerRef}>
      {messages.map((msg, index) => (
        <div key={index}>
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
      ))}
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
