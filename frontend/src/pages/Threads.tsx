import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';
import { useSSE } from '../hooks/useSSE';
import { getThreads, createThread } from '../utils/api';
import { Sidebar } from '../components/Sidebar';
import { IntroSection } from '../components/IntroSection';
import { InputSection } from '../components/InputSection';

export const Threads: React.FC = () => {
  const navigate = useNavigate();
  const { userId, isAuthenticated } = useAuth();
  const { threads, setThreads, clearChat } = useChat();
  const { streamingThreads } = useSSE();
  
  const [showIntro, setShowIntro] = useState(true);
  const [isCreatingThread, setIsCreatingThread] = useState(false);

  // 로그인 체크
  useEffect(() => {
    if (!isAuthenticated) {
      clearChat();
      navigate('/');
    }
  }, [isAuthenticated, navigate, clearChat]);

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

  useEffect(() => {
    if (userId) {
      loadThreadList();
    }
  }, [userId, loadThreadList]);

  // Thread 선택 → URL 변경
  const handleThreadSelect = (threadId: string) => {
    navigate(`/chat/${threadId}`);
  };

  // 새 대화 시작
  const handleNewThread = () => {
    navigate('/chat');
    setShowIntro(true);
  };

  // 홈으로
  const handleGoHome = () => {
    navigate('/chat');
    setShowIntro(true);
  };

  // 메시지 전송 → 새 thread 생성 후 해당 페이지로 이동
  const handleSendMessage = async (message: string) => {
    if (!userId) {
      alert('유저 ID가 설정되지 않았습니다.');
      return;
    }

    setIsCreatingThread(true);

    try {
      // 1. 빈 thread만 먼저 생성
      const newThread = await createThread(userId);
      
      if (newThread) {
        console.log('New thread created:', newThread.thread_id);
        
        // 2. 메시지와 함께 Chat 페이지로 이동
        navigate(`/chat/${newThread.thread_id}`, { 
          state: { initialMessage: message },
          replace: true
        });
      } else {
        throw new Error('Failed to create thread');
      }
    } catch (error) {
      console.error('Error creating thread:', error);
      alert('Thread 생성에 실패했습니다.');
      setIsCreatingThread(false);
    }
  };

  return (
    <>
      <Sidebar
        threads={threads}
        currentThreadId={null}
        streamingThreads={streamingThreads}
        onThreadSelect={handleThreadSelect}
        onNewThread={handleNewThread}
        onGoHome={handleGoHome}
      />

      <main>
        {showIntro ? (
          <IntroSection />
        ) : isCreatingThread ? (
          <div className="chat-section">
            <div className="loading-message" style={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              height: '100%',
              fontSize: '1.1rem',
              color: '#666'
            }}>
              새 대화를 생성하는 중...
            </div>
          </div>
        ) : null}
      </main>

      <InputSection 
        onSend={handleSendMessage} 
        disabled={isCreatingThread}
        isStreaming={false}
      />
    </>
  );
};
