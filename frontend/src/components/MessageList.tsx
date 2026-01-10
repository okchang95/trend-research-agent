import React, { useEffect, useRef } from 'react';
import { Message } from './Message';
import { Message as MessageType } from '../types';

interface MessageListProps {
  messages: MessageType[];
  streamingContent?: string;
  isStreaming?: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  streamingContent,
  isStreaming = false,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 새 메시지가 추가되면 스크롤을 맨 아래로
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingContent]);

  return (
    <div className="messages-container">
      {messages.map((msg, index) => (
        <Message key={index} role={msg.role} content={msg.message} />
      ))}
      {isStreaming && (
        <Message role="assistant" content={streamingContent || ''} isStreaming={true} />
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};
