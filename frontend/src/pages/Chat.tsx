import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useChat } from '../contexts/ChatContext';
import { useSSE } from '../hooks/useSSE';
import { getThreads, getThreadMessages } from '../utils/api';
import { API_BASE_URL } from '../utils/env';
import { Sidebar } from '../components/Sidebar';
import { MessageList } from '../components/MessageList';
import { InputSection } from '../components/InputSection';
import { IntroSection } from '../components/IntroSection';
import { Message, SSEEvent, SearchResult, Finding } from '../types';

export const Chat: React.FC = () => {
  const navigate = useNavigate();
  const { userId, isAuthenticated } = useAuth();
  const { threads, setThreads, currentThreadId, setCurrentThreadId, messages, setMessages, addMessage, clearChat } = useChat();
  const { isStreaming, stream, cancelStream } = useSSE();

  const [showIntro, setShowIntro] = useState(true);
  const [streamingContent, setStreamingContent] = useState('');
  const [nodeStatus, setNodeStatus] = useState<{ name: string; status: 'in_progress' | 'completed' } | null>(null);
  const [researchStatus, setResearchStatus] = useState<{ message: string; results?: SearchResult[] } | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const prevUserIdRef = useRef<string | null>(null);
  const currentThreadIdRef = useRef<string | null>(null);
  const currentStreamingContentRef = useRef<string>('');

  // streamingContent가 변경될 때마다 ref 업데이트
  useEffect(() => {
    currentStreamingContentRef.current = streamingContent;
  }, [streamingContent]);

  // currentThreadId가 변경될 때마다 ref 업데이트
  useEffect(() => {
    currentThreadIdRef.current = currentThreadId;
  }, [currentThreadId]);

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

  // 현재 thread의 generating 상태 확인 및 polling (새로고침/재진입 시 작동)
  useEffect(() => {
    if (!currentThreadId || threads.length === 0 || !userId) return;

    const currentThread = threads.find(t => t.thread_id === currentThreadId);
    
    if (currentThread?.status === 'generating') {
      // 응답 생성 중 표시 (NodeStatus만 사용, streamingContent는 비워둠)
      setStreamingContent('');
      setNodeStatus({ name: 'generating', status: 'in_progress' });
      console.log(`Thread ${currentThreadId} is generating, starting polling`);

      // 3초마다 polling하여 status 확인
      const pollInterval = setInterval(async () => {
        try {
          // Thread list 새로고침
          const threadList = await getThreads(userId);
          const sortedThreads = threadList.sort((a, b) => {
            const dateA = new Date(a.updated_at);
            const dateB = new Date(b.updated_at);
            return dateB.getTime() - dateA.getTime();
          });
          setThreads(sortedThreads);

          // 현재 thread의 status 확인
          const updatedThread = sortedThreads.find(t => t.thread_id === currentThreadId);
          
          if (updatedThread && updatedThread.status !== 'generating') {
            // 생성 완료! 메시지 다시 로드
            console.log(`Thread ${currentThreadId} completed (status: ${updatedThread.status}), reloading messages`);
            
            const threadMessages = await getThreadMessages(currentThreadId);
            const sortedMessages = threadMessages.sort((a, b) => {
              const dateA = new Date(a.timestamp);
              const dateB = new Date(b.timestamp);
              return dateA.getTime() - dateB.getTime();
            });
            setMessages(sortedMessages);
            
            // 상태 초기화
            setStreamingContent('');
            setNodeStatus(null);
            setResearchStatus(null);
            setFindings([]);
            
            console.log('Polling stopped - generation completed');
          }
        } catch (error) {
          console.error('Polling error:', error);
        }
      }, 3000); // 3초마다

      // Cleanup: interval 제거
      return () => {
        console.log(`Polling cleanup for thread ${currentThreadId}`);
        clearInterval(pollInterval);
      };
    } else if (currentThread) {
      // generating 상태가 아니면 초기화
      setStreamingContent('');
      setNodeStatus(null);
    }
  }, [currentThreadId, threads, userId, setThreads, setMessages]);

  // Thread 선택 시 메시지 로드
  const handleThreadSelect = async (threadId: string) => {
    try {
      // 최신 thread list 가져오기
      const threadList = await getThreads(userId!);
      const sortedThreads = threadList.sort((a, b) => {
        const dateA = new Date(a.updated_at);
        const dateB = new Date(b.updated_at);
        return dateB.getTime() - dateA.getTime();
      });
      setThreads(sortedThreads);
      
      const threadMessages = await getThreadMessages(threadId);
      // 시간순으로 정렬
      const sortedMessages = threadMessages.sort((a, b) => {
        const dateA = new Date(a.timestamp);
        const dateB = new Date(b.timestamp);
        return dateA.getTime() - dateB.getTime();
      });
      
      setMessages(sortedMessages);
      setShowIntro(false);
      
      // 선택한 thread의 상태 확인
      const selectedThread = sortedThreads.find(t => t.thread_id === threadId);
      if (selectedThread?.status === 'generating') {
        // 응답 생성 중인 thread를 선택한 경우 (NodeStatus만 사용)
        console.log(`Thread ${threadId} is generating, showing status`);
        setStreamingContent('');
        setNodeStatus({ name: 'generating', status: 'in_progress' });
      } else {
        // 스트리밍 상태 초기화
        setStreamingContent('');
        setNodeStatus(null);
      }
      setResearchStatus(null);
      setFindings([]);
      
      // currentThreadId는 마지막에 설정 (useEffect 트리거)
      setCurrentThreadId(threadId);
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
          // Thread 목록 새로고침 (status를 'completed'로 업데이트)
          loadThreadList();
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
        // Thread 목록 새로고침 (status를 'error'로 업데이트)
        loadThreadList();
        break;

      default:
        console.warn('Unknown event type:', event.type);
    }
  }, [currentThreadId, addMessage, loadThreadList, setCurrentThreadId]);

  // 스트림 중지 핸들러
  const handleStopStream = useCallback(async () => {
    // SSE 연결 취소
    cancelStream();
    
    const threadId = currentThreadIdRef.current;
    
    if (threadId && userId) {
      try {
        // 백그라운드 task 취소 (agent 실행 중지)
        // Backend에서 자동으로 "[응답이 중지되었습니다]" 메시지 저장
        await fetch(`${API_BASE_URL}/api/chat/cancel-task`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            thread_id: threadId,
          }),
        });
        
        // Thread 목록 새로고침
        await loadThreadList();
        
        // 메시지 다시 로드
        if (threadId) {
          const threadMessages = await getThreadMessages(threadId);
          const sortedMessages = threadMessages.sort((a, b) => {
            const dateA = new Date(a.timestamp);
            const dateB = new Date(b.timestamp);
            return dateA.getTime() - dateB.getTime();
          });
          setMessages(sortedMessages);
        }
      } catch (error) {
        console.error('Failed to cancel stream:', error);
      }
    }
    
    // 스트리밍 상태 초기화
    setStreamingContent('');
    setNodeStatus(null);
    setResearchStatus(null);
    setFindings([]);
  }, [cancelStream, userId, loadThreadList, setMessages]);

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

  // 현재 thread의 generating 상태 확인
  const currentThread = threads.find(t => t.thread_id === currentThreadId);
  const isGenerating = currentThread?.status === 'generating';

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

      <InputSection 
        onSend={handleSendMessage} 
        onStop={handleStopStream}
        disabled={isStreaming || isGenerating}
        isStreaming={isStreaming || isGenerating}
      />
    </>
  );
};
