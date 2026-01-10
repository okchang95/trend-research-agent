import React, { useState, useEffect } from 'react';
import { Thread } from '../types';
import { useAuth } from '../contexts/AuthContext';

interface SidebarProps {
  threads: Thread[];
  currentThreadId: string | null;
  onThreadSelect: (threadId: string) => void;
  onNewThread: () => void;
  onGoHome: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  threads,
  currentThreadId,
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
      // 모바일로 전환되면 사이드바 닫기
      if (mobile && isOpen) {
        setIsOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    // 초기 상태 설정
    handleResize();
    
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

  const toggleSidebar = () => {
    setIsOpen(!isOpen);
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
        aria-label="메뉴 열기"
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
      <aside className={`sidebar ${sidebarIsOpen ? 'open' : 'closed'}`} id="sidebar">

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
              threads.map((thread) => (
                <div
                  key={thread.thread_id}
                  className={`thread-item ${currentThreadId === thread.thread_id ? 'active' : ''}`}
                  onClick={() => handleThreadClick(thread.thread_id)}
                >
                  <div className="thread-title">{thread.title}</div>
                </div>
              ))
            )}
          </div>
        </div>
      </aside>
    </>
  );
};
