import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';
import { useSSE } from '../hooks/useSSE';
import { getThreads } from '../utils/api';
import { Sidebar } from '../components/Sidebar';
import { IntroSection } from '../components/IntroSection';
import { InputSection } from '../components/InputSection';
import { SSEEvent } from '../types';

export const Threads: React.FC = () => {
  const navigate = useNavigate();
  const { userId, isAuthenticated } = useAuth();
  const { threads, setThreads, clearChat } = useChat();
  const { stream } = useSSE();
  
  const [showIntro, setShowIntro] = useState(true);

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

    setShowIntro(false);

    const requestBody = {
      user_id: userId,
      user_message: message,
      // thread_id 없음 → 백엔드에서 새로 생성
    };

    try {
      // SSE 이벤트 핸들러
      const handleSSEEvent = (event: SSEEvent) => {
        if (event.type === 'thread') {
          // 새 thread 생성됨 → 해당 페이지로 이동
          const newThreadId = event.thread_id;
          console.log('New thread created:', newThreadId);
          navigate(`/chat/${newThreadId}`, { replace: true });
        }
      };

      await stream('new', requestBody, handleSSEEvent);
    } catch (error) {
      console.error('Stream error:', error);
      alert('스트리밍 중 오류가 발생했습니다.');
      setShowIntro(true);
    }
  };

  return (
    <>
      <Sidebar
        threads={threads}
        currentThreadId={null}
        onThreadSelect={handleThreadSelect}
        onNewThread={handleNewThread}
        onGoHome={handleGoHome}
      />

      <main>
        {showIntro ? (
          <IntroSection />
        ) : (
          <div className="chat-section">
            <div className="loading-message" style={{ 
              display: 'flex', 
              justifyContent: 'center', 
              alignItems: 'center', 
              height: '100%',
              fontSize: '1.1rem',
              color: '#666'
            }}>
              새 대화를 시작하는 중...
            </div>
          </div>
        )}
      </main>

      <InputSection 
        onSend={handleSendMessage} 
        disabled={false}
        isStreaming={false}
      />
    </>
  );
};
