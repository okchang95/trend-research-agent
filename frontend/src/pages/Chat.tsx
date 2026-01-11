import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';
import { useSSE } from '../hooks/useSSE';
import { getThreads, getThreadMessages } from '../utils/api';
import { API_BASE_URL } from '../utils/env';
import { Sidebar } from '../components/Sidebar';
import { MessageList } from '../components/MessageList';
import { InputSection } from '../components/InputSection';
import { Message, SSEEvent, SearchResult, Finding } from '../types';

export const Chat: React.FC = () => {
  const { threadId } = useParams<{ threadId: string }>();
  const navigate = useNavigate();
  const { userId, isAuthenticated } = useAuth();
  const { threads, setThreads, setMessages, addMessage } = useChat();
  const { isThreadStreaming, stream, cancelStream } = useSSE();

  const [messages, setLocalMessages] = useState<Message[]>([]);
  const [streamingContent, setStreamingContent] = useState('');
  const [nodeStatus, setNodeStatus] = useState<{ name: string; status: 'in_progress' | 'completed' } | null>(null);
  const [researchStatus, setResearchStatus] = useState<{ message: string; results?: SearchResult[] } | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);

  // 로그인 체크
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate]);

  // Thread 목록 로드
  const loadThreadList = useCallback(async () => {
    if (!userId) return;
    try {
      const threadList = await getThreads(userId);
      const sortedThreads = threadList.sort((a, b) => {
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
      });
      setThreads(sortedThreads);
    } catch (error) {
      console.error('Error loading threads:', error);
    }
  }, [userId, setThreads]);

  // Thread 메시지 로드
  const loadThreadMessages = useCallback(async (tid: string) => {
    if (!userId) return;
    try {
      const threadMessages = await getThreadMessages(tid, userId);
      const sortedMessages = threadMessages.sort((a, b) => {
        return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
      });
      setLocalMessages(sortedMessages);
      setMessages(sortedMessages);
      
      // 스트리밍 상태 초기화
      setStreamingContent('');
      setResearchStatus(null);
      setFindings([]);
    } catch (error) {
      console.error('Error loading messages:', error);
      alert('메시지를 불러올 수 없습니다.');
    }
  }, [userId, setMessages]);

  // 초기 로드
  useEffect(() => {
    if (userId) {
      loadThreadList();
    }
  }, [userId, loadThreadList]);

  // Thread 메시지 로드 (threadId 변경 시)
  useEffect(() => {
    if (threadId && userId) {
      loadThreadMessages(threadId);
    }
  }, [threadId, userId, loadThreadMessages]);

  // Thread 유효성 검사
  useEffect(() => {
    if (threads.length > 0 && threadId) {
      const exists = threads.some(t => t.thread_id === threadId);
      if (!exists) {
        alert('존재하지 않는 대화입니다.');
        navigate('/chat');
      }
    }
  }, [threads, threadId, navigate]);

  // Generating 상태 확인 및 polling
  useEffect(() => {
    if (!threadId || threads.length === 0 || !userId) return;

    const currentThread = threads.find(t => t.thread_id === threadId);
    
    // 스트리밍 중이 아니고, generating 상태면 polling 시작
    if (!isThreadStreaming(threadId) && currentThread?.status === 'generating') {
      setNodeStatus({ name: 'generating', status: 'in_progress' });
      console.log(`Thread ${threadId} is generating (re-entered), starting polling`);
      
      const pollInterval = setInterval(async () => {
        try {
          const threadList = await getThreads(userId);
          const updatedThread = threadList.find(t => t.thread_id === threadId);
          
          if (updatedThread?.status !== 'generating') {
            clearInterval(pollInterval);
            setNodeStatus(null);
            console.log(`Thread ${threadId} completed, reloading messages`);
            
            // 메시지 재로드
            await loadThreadMessages(threadId);
            
            // Thread 목록 업데이트
            const sortedThreads = threadList.sort((a, b) => {
              return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
            });
            setThreads(sortedThreads);
          }
        } catch (error) {
          console.error('Polling error:', error);
        }
      }, 3000);

      return () => clearInterval(pollInterval);
    }
  }, [threadId, threads, userId, isThreadStreaming, loadThreadMessages, setThreads]);

  // 페이지 제목 업데이트
  useEffect(() => {
    const currentThread = threads.find(t => t.thread_id === threadId);
    if (currentThread) {
      document.title = `${currentThread.title} - Trend Agent`;
    }
    return () => {
      document.title = 'Trend Agent';
    };
  }, [threads, threadId]);

  // Thread 선택 → URL 변경
  const handleThreadSelect = (selectedThreadId: string) => {
    navigate(`/chat/${selectedThreadId}`);
  };

  // 새 대화
  const handleNewThread = () => {
    navigate('/chat');
  };

  // 홈으로
  const handleGoHome = () => {
    navigate('/chat');
  };

  // SSE 이벤트 처리
  const handleSSEEvent = useCallback((event: SSEEvent) => {
    console.log('SSE Event:', event);

    switch (event.type) {
      case 'node_start':
        setNodeStatus({ name: event.node, status: 'in_progress' });
        break;

      case 'node_complete':
        setNodeStatus({ name: event.node, status: 'completed' });
        setTimeout(() => setNodeStatus(null), 1000);
        break;

      case 'research_status':
        setResearchStatus({
          message: event.message,
          results: event.results,
        });
        break;

      case 'research_findings':
        console.log('Research findings:', event.findings);
        setFindings(event.findings || []);
        break;

      case 'text_chunk':
        setStreamingContent(prev => prev + event.char);
        break;

      case 'final':
        const finalMessage: Message = {
          thread_id: threadId!,
          role: 'assistant',
          message: event.state.answer,
          timestamp: new Date().toISOString(),
        };
        setLocalMessages(prev => [...prev, finalMessage]);
        addMessage(finalMessage);
        setStreamingContent('');
        setNodeStatus(null);
        setResearchStatus(null);
        
        // Thread 목록 새로고침
        loadThreadList();
        break;

      case 'error':
        console.error('Agent error:', event.error);
        alert('에러가 발생했습니다: ' + event.error);
        setStreamingContent('');
        setNodeStatus(null);
        setResearchStatus(null);
        setFindings([]);
        break;
    }
  }, [threadId, addMessage, loadThreadList]);

  // 메시지 전송
  const handleSendMessage = async (message: string) => {
    if (!userId || !threadId) {
      alert('유저 ID 또는 Thread ID가 설정되지 않았습니다.');
      return;
    }

    const userMessage: Message = {
      thread_id: threadId,
      role: 'user',
      message: message,
      timestamp: new Date().toISOString(),
    };
    setLocalMessages(prev => [...prev, userMessage]);
    addMessage(userMessage);

    setStreamingContent('');
    setNodeStatus(null);
    setResearchStatus(null);
    setFindings([]);

    const requestBody = {
      user_id: userId,
      thread_id: threadId,
      user_message: message,
    };

    try {
      await stream(threadId, requestBody, handleSSEEvent);
    } catch (error) {
      console.error('Stream error:', error);
      alert('스트리밍 중 오류가 발생했습니다.');
    }
  };

  // 중지
  const handleStopStream = useCallback(async () => {
    if (!threadId) return;

    cancelStream(threadId);

    try {
      await fetch(`${API_BASE_URL}/api/chat/cancel-task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ thread_id: threadId }),
      });

      await loadThreadList();
      await loadThreadMessages(threadId);
    } catch (error) {
      console.error('Failed to cancel:', error);
    }

    setStreamingContent('');
    setNodeStatus(null);
    setResearchStatus(null);
    setFindings([]);
  }, [threadId, cancelStream, loadThreadList, loadThreadMessages]);

  // 현재 thread 상태
  const currentThread = threads.find(t => t.thread_id === threadId);
  const isStreaming = threadId ? isThreadStreaming(threadId) : false;
  const isGenerating = currentThread?.status === 'generating';
  const isInputDisabled = isStreaming || isGenerating;

  if (!threadId) {
    return <div>Invalid thread ID</div>;
  }

  return (
    <>
      <Sidebar
        threads={threads}
        currentThreadId={threadId}
        onThreadSelect={handleThreadSelect}
        onNewThread={handleNewThread}
        onGoHome={handleGoHome}
      />

      <main>
        <div className="chat-section">
          <MessageList
            messages={messages}
            streamingContent={streamingContent}
            isStreaming={isStreaming}
            nodeStatus={nodeStatus}
            researchStatus={researchStatus}
            findings={findings}
          />
        </div>
      </main>

      <InputSection 
        onSend={handleSendMessage} 
        onStop={handleStopStream}
        disabled={isInputDisabled}
        isStreaming={isStreaming}
      />
    </>
  );
};
