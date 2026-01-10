import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';
import { useSSE } from '../hooks/useSSE';
import { getThreads, getThreadMessages } from '../utils/api';
import { Sidebar } from '../components/Sidebar';
import { MessageList } from '../components/MessageList';
import { InputSection } from '../components/InputSection';
import { IntroSection } from '../components/IntroSection';
import { Message, SSEEvent, SearchResult, Finding } from '../types';

export const Chat: React.FC = () => {
  const navigate = useNavigate();
  const { userId, isAuthenticated } = useAuth();
  const { threads, setThreads, currentThreadId, setCurrentThreadId, messages, setMessages, addMessage, clearChat } = useChat();
  const { isStreaming, stream } = useSSE();

  const [showIntro, setShowIntro] = useState(true);
  const [streamingContent, setStreamingContent] = useState('');
  const [nodeStatus, setNodeStatus] = useState<{ name: string; status: 'in_progress' | 'completed' } | null>(null);
  const [researchStatus, setResearchStatus] = useState<{ message: string; results?: SearchResult[] } | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const prevUserIdRef = useRef<string | null>(null);

  // 로그인 상태 확인 및 로그아웃 시 채팅 데이터 초기화
  useEffect(() => {
    if (!isAuthenticated) {
      clearChat();
      navigate('/');
    }
  }, [isAuthenticated, navigate, clearChat]);

  // Thread 리스트 로드
  const loadThreadList = useCallback(async () => {
    if (!userId) return;

    try {
      const threadList = await getThreads(userId);
      // updated_at 기준 최신순 정렬
      const sortedThreads = threadList.sort((a, b) => {
        const dateA = new Date(a.updated_at);
        const dateB = new Date(b.updated_at);
        return dateB.getTime() - dateA.getTime();
      });
      setThreads(sortedThreads);
    } catch (error) {
      console.error('Error loading threads:', error);
    }
  }, [userId, setThreads]);

  // 초기 Thread 리스트 로드 및 userId 변경 시 이전 데이터 초기화
  useEffect(() => {
    if (userId) {
      // userId가 실제로 변경되었을 때만 이전 데이터 초기화
      if (prevUserIdRef.current !== null && prevUserIdRef.current !== userId) {
        clearChat();
      }
      prevUserIdRef.current = userId;
      
      // 새 유저의 thread 목록 로드
      loadThreadList();
    }
  }, [userId, loadThreadList, clearChat]);

  // Thread 선택 시 메시지 로드
  const handleThreadSelect = async (threadId: string) => {
    try {
      const threadMessages = await getThreadMessages(threadId);
      // 시간순으로 정렬
      const sortedMessages = threadMessages.sort((a, b) => {
        const dateA = new Date(a.timestamp);
        const dateB = new Date(b.timestamp);
        return dateA.getTime() - dateB.getTime();
      });
      
      setMessages(sortedMessages);
      setCurrentThreadId(threadId);
      setShowIntro(false);
      // 스트리밍 상태 초기화
      setStreamingContent('');
      setNodeStatus(null);
      setResearchStatus(null);
      setFindings([]);
    } catch (error) {
      console.error('Error loading messages:', error);
      alert('메시지를 불러올 수 없습니다.');
    }
  };

  // 새 Thread 시작 (thread는 첫 메시지 전송 시 백엔드에서 생성)
  const handleNewThread = () => {
    setMessages([]);
    setCurrentThreadId(null);
    setShowIntro(true);
    setStreamingContent('');
    setNodeStatus(null);
    setResearchStatus(null);
    setFindings([]);
  };

  // 홈으로 돌아가기 (대화 시작 전 상태)
  const handleGoHome = () => {
    setShowIntro(true);
    setMessages([]);
    setCurrentThreadId(null);
    setStreamingContent('');
    setNodeStatus(null);
    setResearchStatus(null);
    setFindings([]);
  };

  // SSE 이벤트 처리
  const handleSSEEvent = useCallback((event: SSEEvent) => {
    console.log('SSE Event:', event);

    switch (event.type) {
      case 'thread':
        // Thread ID 업데이트 (첫 채팅 시)
        if (event.thread_id) {
          setCurrentThreadId(event.thread_id);
          loadThreadList();
        }
        break;

      case 'session':
        // Session ID 저장
        console.log('Session ID:', event.session_id);
        break;

      case 'scoping_complete':
        // 명확화 완료
        console.log('Scoping complete');
        break;

      case 'node_start':
        // 노드 시작
        console.log('Node start:', event.node);
        if (event.node !== 'clarify_requirement') {
          setNodeStatus({ name: event.node, status: 'in_progress' });
        }
        break;

      case 'node_complete':
        // 노드 완료
        console.log('Node complete:', event.node);
        if (event.node !== 'clarify_requirement') {
          setNodeStatus({ name: event.node, status: 'completed' });
          // 완료 후 일정 시간 후 상태 초기화 (선택사항)
          setTimeout(() => {
            setNodeStatus(null);
          }, 2000);
        }
        break;

      case 'research_status':
        // 조사 상태 업데이트
        console.log('Research status:', event.message);
        setResearchStatus({
          message: event.message,
          results: event.results || []
        });
        break;

      case 'research_findings':
        // 조사 결과
        console.log('Research findings:', event.findings);
        setFindings(event.findings || []);
        // research status 숨기기
        setResearchStatus(null);
        break;

      case 'text_chunk':
        // 텍스트 청크 스트리밍
        setStreamingContent((prev) => prev + event.char);
        break;

      case 'final':
        // 최종 응답
        if (event.state?.answer) {
          const assistantMessage: Message = {
            thread_id: currentThreadId || '',
            role: 'assistant',
            message: event.state.answer,
            timestamp: new Date().toISOString(),
          };
          addMessage(assistantMessage);
          setStreamingContent('');
          // 스트리밍 관련 상태 초기화
          setNodeStatus(null);
          setResearchStatus(null);
          setFindings([]);
        }
        break;

      case 'error':
        // 에러 처리
        console.error('SSE Error:', event.error);
        alert('오류가 발생했습니다: ' + event.error);
        setStreamingContent('');
        // 에러 시 스트리밍 관련 상태 초기화
        setNodeStatus(null);
        setResearchStatus(null);
        setFindings([]);
        break;

      default:
        console.warn('Unknown event type:', event.type);
    }
  }, [currentThreadId, addMessage, loadThreadList, setCurrentThreadId]);

  // 메시지 전송
  const handleSendMessage = async (message: string) => {
    if (!userId) {
      alert('유저 ID가 설정되지 않았습니다.');
      return;
    }

    // 첫 대화인 경우 인트로 숨기기
    if (messages.length === 0) {
      setShowIntro(false);
    }

    // 사용자 메시지 추가
    const userMessage: Message = {
      thread_id: currentThreadId || '',
      role: 'user',
      message: message,
      timestamp: new Date().toISOString(),
    };
    addMessage(userMessage);

    // 스트리밍 초기화
    setStreamingContent('');
    setNodeStatus(null);
    setResearchStatus(null);
    setFindings([]);

    // SSE 요청 바디 구성
    const requestBody: any = {
      user_id: userId,
      user_message: message,
    };

    // 현재 thread_id가 있으면 추가
    if (currentThreadId) {
      requestBody.thread_id = currentThreadId;
    }

    try {
      await stream(requestBody, handleSSEEvent);
    } catch (error) {
      console.error('Stream error:', error);
      alert('스트리밍 중 오류가 발생했습니다.');
    }
  };

  return (
    <>
      <Sidebar
        threads={threads}
        currentThreadId={currentThreadId}
        onThreadSelect={handleThreadSelect}
        onNewThread={handleNewThread}
        onGoHome={handleGoHome}
      />

      <main>
        {showIntro && messages.length === 0 ? (
          <IntroSection />
        ) : (
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
        )}
      </main>

      <InputSection onSend={handleSendMessage} disabled={isStreaming} />
    </>
  );
};
