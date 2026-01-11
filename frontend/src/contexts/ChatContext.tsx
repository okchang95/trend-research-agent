import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { Thread, Message } from '../types';

interface ChatContextType {
  threads: Thread[];
  setThreads: (threads: Thread[]) => void;
  currentThreadId: string | null;
  setCurrentThreadId: (threadId: string | null) => void;
  messages: Message[];
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  clearChat: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [currentThreadId, setCurrentThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

  const addMessage = useCallback((message: Message) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  const clearChat = useCallback(() => {
    setThreads([]);
    setCurrentThreadId(null);
    setMessages([]);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        threads,
        setThreads,
        currentThreadId,
        setCurrentThreadId,
        messages,
        setMessages,
        addMessage,
        clearChat,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};
