import React, { useState, useEffect } from 'react';
import { Thread } from '../types';
import { useAuth } from '../contexts/AuthContext';

interface SidebarProps {
  threads: Thread[];
  currentThreadId: string | null;
  streamingThreads: Set<string>;
  onThreadSelect: (threadId: string) => void;
  onNewThread: () => void;
  onGoHome: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  threads,
  currentThreadId,
  streamingThreads,
  onThreadSelect,
  onNewThread,
  onGoHome,
}) => {
  const { userName, logout } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

  // 리사이즈 이벤트 감지
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
      // 데스크탑으로 전환되면 사이드바 열기, 모바일로 전환되면 닫기
      if (!mobile) {
        // 데스크탑: 항상 열림
        setIsOpen(false); // isOpen은 모바일 전용이므로 false로 유지
      } else if (mobile && isOpen) {
        // 모바일로 전환될 때 열려있으면 닫기
        // setIsOpen은 그대로 유지 (사용자가 열어둔 상태면 유지)
      }
    };

    window.addEventListener('resize', handleResize);
    // 초기 상태 설정
    const initialMobile = window.innerWidth <= 768;
    setIsMobile(initialMobile);
    
    return () => window.removeEventListener('resize', handleResize);
  }, [isOpen]);

  const handleGoHome = () => {
    onGoHome();
    // 모바일에서는 사이드바 닫기
    if (isMobile) {
      closeSidebar();
    }
  };

  const handleLogout = () => {
    if (window.confirm('로그아웃 하시겠습니까?')) {
      logout();
    }
  };

  const toggleSidebar = (e?: React.MouseEvent) => {
    e?.stopPropagation();
    setIsOpen(prev => !prev);
  };

  const closeSidebar = () => {
    setIsOpen(false);
  };

  const handleThreadClick = (threadId: string) => {
    onThreadSelect(threadId);
    // 모바일에서는 사이드바 닫기
    if (isMobile) {
      closeSidebar();
    }
  };

  const handleNewThread = () => {
    onNewThread();
    // 모바일에서는 사이드바 닫기
    if (isMobile) {
      closeSidebar();
    }
  };

  // 데스크탑에서는 항상 열림, 모바일에서는 토글 상태
  const sidebarIsOpen = !isMobile || isOpen;

  return (
    <>
      {/* 작은 햄버거 메뉴 버튼 */}
      <button
        className={`menu-toggle ${isOpen && isMobile ? 'active' : ''}`}
        onClick={toggleSidebar}
        aria-label={isOpen ? '메뉴 닫기' : '메뉴 열기'}
        type="button"
      >
        <span></span>
        <span></span>
        <span></span>
      </button>

      {/* 사이드바 오버레이 (모바일용) */}
      <div
        id="sidebarOverlay"
        className={`sidebar-overlay ${isOpen && isMobile ? 'active' : ''}`}
        onClick={closeSidebar}
      ></div>

      {/* 사이드바 */}
      <aside 
        className={`sidebar ${sidebarIsOpen ? 'open' : 'closed'}`} 
        id="sidebar"
      >

        <div className="sidebar-header">
          <h1 
            onClick={handleGoHome}
            style={{ cursor: 'pointer' }}
            title="홈으로 돌아가기"
          >
            Trend Agent demo
          </h1>
          <div className="sidebar-user-info">
            <span className="user-name-display">{userName}</span>
            <button onClick={handleLogout} className="logout-btn" title="로그아웃">
              로그아웃
            </button>
          </div>
          <button onClick={handleNewThread} className="new-thread-btn">
            + 새 대화
          </button>
        </div>
        <div className="sidebar-content">
          <div className="thread-list">
            {threads.length === 0 ? (
              <div style={{ padding: '20px', textAlign: 'center', color: 'rgba(255,255,255,0.7)' }}>
                Thread가 없습니다.
              </div>
            ) : (
              threads.map((thread) => {
                const isActive = currentThreadId === thread.thread_id;
                const isStreaming = streamingThreads.has(thread.thread_id);
                const isGenerating = thread.status === 'generating';
                
                return (
                  <div
                    key={thread.thread_id}
                    className={`thread-item ${isActive ? 'active' : ''}`}
                    onClick={() => handleThreadClick(thread.thread_id)}
                  >
                    <div className="thread-title">{thread.title}</div>
                    {(isStreaming || isGenerating) && (
                      <div className="thread-status">
                        <span className="loading-spinner">⏳</span>
                        {isStreaming ? ' 스트리밍 중' : ' 실행 중'}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        </div>
      </aside>
    </>
  );
};
