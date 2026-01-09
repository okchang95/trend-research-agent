/**
 * 메인 애플리케이션 파일
 * 모듈화된 컴포넌트들을 조합하여 애플리케이션 초기화
 */

// API 엔드포인트 설정
// .env 파일에서 환경 변수 읽기 (window.__ENV__에 설정됨)
// 프로덕션 환경에서는 항상 같은 origin 사용 (nginx 프록시를 통해)
const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocalDev 
    ? (window.__ENV__?.API_BASE_URL || 'http://localhost:8000')
    : window.location.origin; // 프로덕션: 같은 origin 사용 (nginx 프록시)
const API_STREAM_URL = API_BASE_URL + '/api/chat/stream';
const API_THREADS_URL = API_BASE_URL + '/api/threads';
const API_MESSAGES_URL = API_BASE_URL + '/api/threads';
const API_USERS_URL = API_BASE_URL + '/api/users';

// DOM 요소
const userInput = document.getElementById('userInput');
const searchBtn = document.getElementById('searchBtn');
const messagesContainer = document.getElementById('messagesContainer');
const introSection = document.getElementById('introSection');
const chatSection = document.getElementById('chatSection');
const threadList = document.getElementById('threadList');
const newThreadBtn = document.getElementById('newThreadBtn');
const currentUserName = document.getElementById('currentUserName');
const logoutBtn = document.getElementById('logoutBtn');

// 상태 관리 및 모듈 초기화
const stateManager = new StateManager();
const uiUpdater = new UIUpdater(stateManager, messagesContainer);
const eventHandlers = new EventHandlers(stateManager, uiUpdater);
const sseClient = new SSEClient(API_STREAM_URL);

// 현재 스트림 상태
let currentEventSource = null;

// 페이지 로드 시 초기화
window.addEventListener('DOMContentLoaded', () => {
    // 햄버거 메뉴 토글 (모바일용)
    initMobileMenu();
    
    // 로그아웃 버튼 이벤트 리스너
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }
    
    // 새 대화 버튼 이벤트
    if (newThreadBtn) {
        newThreadBtn.addEventListener('click', handleNewThread);
    }
    
    // 로그인 상태 확인
    const userName = localStorage.getItem('userId'); // 실제로는 user_name이 저장됨
    if (userName) {
        // 로그인된 상태면 메인 페이지 초기화
        showMainPage(userName).catch(error => {
            console.error('Error initializing main page:', error);
            alert('페이지 초기화 중 오류가 발생했습니다: ' + error.message);
            window.location.href = '/landing.html';
        });
    } else {
        // 로그인 안 된 상태면 렌딩 페이지로 리다이렉트
        window.location.href = '/landing.html';
    }
});

/**
 * 메인 페이지 표시
 */
async function showMainPage(userName) {
    try {
        // 1. 유저 이름으로 user_id 조회
        const userResponse = await fetch(`${API_USERS_URL}?name=${encodeURIComponent(userName)}`);
        const userResult = await userResponse.json();
        
        if (!userResult.success || !userResult.data) {
            console.error('Failed to get user:', userResult.message);
            alert('유저를 찾을 수 없습니다.');
            window.location.href = '/landing.html';
            return;
        }
        
        const userId = userResult.data.user_id || userResult.data.id;
        if (!userId) {
            console.error('User ID is undefined. User result:', userResult);
            alert('유저 ID를 찾을 수 없습니다.');
            window.location.href = '/landing.html';
            return;
        }
        
        // 2. user_id를 stateManager에 저장 (user_id는 ObjectId 문자열)
        stateManager.setUserId(userId);
        // 사용자 이름은 별도로 저장 (표시용)
        stateManager.setUserName(userName);
        
        // 3. UI에 사용자 이름 표시
        const userNameDisplay = document.getElementById('currentUserName');
        if (userNameDisplay) {
            userNameDisplay.textContent = userName;
        }
        
        // 4. Thread 리스트 로드
        loadThreads();
    } catch (error) {
        console.error('Error in showMainPage:', error);
        alert('페이지 초기화 중 오류가 발생했습니다.');
        window.location.href = '/landing.html';
    }
}

/**
 * 로그아웃 처리
 */
function handleLogout() {
    if (confirm('로그아웃 하시겠습니까?')) {
        localStorage.removeItem('userId');
        stateManager.setUserId(null);
        window.location.href = '/landing.html';
    }
}

// 검색 버튼 클릭 이벤트
if (searchBtn) {
    searchBtn.addEventListener('click', handleSearch);
}

// Enter 키 이벤트
if (userInput) {
    userInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !searchBtn.disabled) {
            handleSearch();
        }
    });
}

// 이벤트 리스너는 DOMContentLoaded에서 등록됨

/**
 * 검색 처리 함수
 */
async function handleSearch() {
    const message = userInput.value.trim();
    
    if (!message) {
        alert('메시지를 입력해주세요.');
        return;
    }
    
    // 첫 대화인 경우 소개 섹션 숨기고 대화창 표시
    if (stateManager.getHistory().length === 0) {
        introSection.style.display = 'none';
        chatSection.style.display = 'block';
    }
    
    // 기존 스트림이 있으면 종료
    if (currentEventSource) {
        currentEventSource.close();
    }
    
    // 사용자 메시지 추가
    const userMessageElement = addUserMessage(message, messagesContainer);
    stateManager.addToHistory('user', message);
    
    // 입력 필드 초기화
    userInput.value = '';
    
    // UI 상태 업데이트
    uiUpdater.setLoadingState();
    stateManager.resetStreamingState();
    
    // 어시스턴트 메시지 영역 생성
    const messageId = 'msg-' + Date.now();
    stateManager.setCurrentMessageId(messageId);
    addAssistantMessage('', messageId, messagesContainer);
    
    // "생각중..." 표시를 위한 타이머 시작
    uiUpdater.startThinkingTimer();
    
    // 사용자 메시지 추가 후 해당 메시지로 스크롤
    setTimeout(() => {
        uiUpdater.scrollToMessage(userMessageElement);
    }, 100);
    
    try {
        // SSE를 사용한 스트리밍 요청
        await streamAgent(message);
    } catch (error) {
        console.error('Error:', error);
        uiUpdater.displayErrorMessage(error.message);
        uiUpdater.resetButtonState();
    }
}

/**
 * Thread 리스트 로드
 */
async function loadThreads() {
    const userId = stateManager.getUserId(); // user_id (ObjectId 문자열)
    if (!userId) {
        console.error('User ID is not set');
        threadList.innerHTML = '<div style="padding: 20px; text-align: center; color: rgba(255,255,255,0.7);">유저 ID가 설정되지 않았습니다.</div>';
        return;
    }
    
    try {
        // user_id로 thread 리스트 조회
        const threadsResponse = await fetch(`${API_THREADS_URL}?user_id=${encodeURIComponent(userId)}`);
        const threadsResult = await threadsResponse.json();
        
        console.log('Threads response:', threadsResult);
        
        if (threadsResult.success) {
            const threads = threadsResult.data || [];
            
            if (threads.length === 0) {
                threadList.innerHTML = '<div style="padding: 20px; text-align: center; color: rgba(255,255,255,0.7);">Thread가 없습니다.</div>';
                return;
            }
            
            // updated_at 기준 최신순 정렬
            const sortedThreads = threads.sort((a, b) => {
                const dateA = new Date(a.updated_at);
                const dateB = new Date(b.updated_at);
                return dateB - dateA;
            });
            
            renderThreadList(sortedThreads);
        } else {
            console.error('Failed to load threads:', threadsResult);
            threadList.innerHTML = '<div style="padding: 20px; text-align: center; color: rgba(255,255,255,0.7);">Thread를 불러올 수 없습니다: ' + (threadsResult.message || '알 수 없는 오류') + '</div>';
        }
    } catch (error) {
        console.error('Error loading threads:', error);
        threadList.innerHTML = '<div style="padding: 20px; text-align: center; color: rgba(255,255,255,0.7);">Thread를 불러올 수 없습니다: ' + error.message + '</div>';
    }
}

/**
 * Thread 리스트 렌더링
 */
function renderThreadList(threads) {
    threadList.innerHTML = '';
    
    if (threads.length === 0) {
        threadList.innerHTML = '<div style="padding: 20px; text-align: center; color: rgba(255,255,255,0.7);">Thread가 없습니다.</div>';
        return;
    }
    
    const currentThreadId = stateManager.getCurrentThreadId();
    
    threads.forEach(thread => {
        const threadItem = document.createElement('div');
        threadItem.className = 'thread-item';
        threadItem.dataset.threadId = thread.thread_id;
        if (currentThreadId === thread.thread_id) {
            threadItem.classList.add('active');
        }
        threadItem.innerHTML = `<div class="thread-title">${escapeHtml(thread.title)}</div>`;
        threadItem.addEventListener('click', () => {
            loadThreadMessages(thread.thread_id);
        });
        threadList.appendChild(threadItem);
    });
}

/**
 * 새 대화 시작
 */
async function handleNewThread() {
    const userId = stateManager.getUserId(); // user_id (ObjectId 문자열)
    if (!userId) {
        alert('유저 ID가 설정되지 않았습니다.');
        return;
    }
    
    try {
        const response = await fetch(API_THREADS_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: userId })
        });
        
        const result = await response.json();
        
        if (result.success && result.data) {
            const threadId = result.data.thread_id;
            // Thread 리스트 새로고침
            await loadThreads();
            // 새로 생성된 thread의 메시지 로드 (빈 상태)
            await loadThreadMessages(threadId);
            // 입력 필드 포커스
            userInput.focus();
        } else {
            alert('새 대화를 시작할 수 없습니다: ' + (result.message || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('Error creating thread:', error);
        alert('새 대화를 시작할 수 없습니다.');
    }
}

/**
 * Thread 메시지 로드
 */
async function loadThreadMessages(threadId) {
    try {
        stateManager.setCurrentThreadId(threadId);
        
        // 활성 thread 표시 업데이트
        document.querySelectorAll('.thread-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.threadId === threadId) {
                item.classList.add('active');
            }
        });
        
        const response = await fetch(`${API_MESSAGES_URL}/${threadId}/messages`);
        const result = await response.json();
        
        if (result.success && result.data) {
            // 메시지 컨테이너 초기화
            messagesContainer.innerHTML = '';
            stateManager.conversationHistory = [];
            
            // 메시지들을 시간순으로 정렬
            const messages = result.data.sort((a, b) => {
                const dateA = new Date(a.timestamp);
                const dateB = new Date(b.timestamp);
                return dateA - dateB;
            });
            
            // 메시지 렌더링
            messages.forEach(message => {
                if (message.role === 'user') {
                    addUserMessage(message.message, messagesContainer);
                    stateManager.addToHistory('user', message.message);
                } else if (message.role === 'assistant') {
                    const messageId = 'msg-' + Date.now() + '-' + Math.random();
                    addAssistantMessage(message.message, messageId, messagesContainer);
                    stateManager.addToHistory('assistant', message.message);
                }
            });
            
            // 소개 섹션 숨기고 채팅 섹션 표시
            introSection.style.display = 'none';
            chatSection.style.display = 'block';
            
            // 스크롤을 맨 아래로
            setTimeout(() => {
                window.scrollTo({
                    top: document.body.scrollHeight,
                    behavior: 'smooth'
                });
            }, 100);
        } else {
            console.error('Failed to load messages:', result.message);
            alert('메시지를 불러올 수 없습니다.');
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        alert('메시지를 불러올 수 없습니다.');
    }
}

/**
 * SSE 스트리밍 에이전트 실행
 */
async function streamAgent(message) {
    const userId = stateManager.getUserId();
    if (!userId) {
        alert('유저 ID가 설정되지 않았습니다.');
        return;
    }
    
    const requestBody = {
        user_id: userId,
        user_message: message
    };
    
    // 현재 thread_id가 있으면 추가 (첫 대화가 아닌 경우)
    const currentThreadId = stateManager.getCurrentThreadId();
    if (currentThreadId) {
        requestBody.thread_id = currentThreadId;
    }
    
    try {
        await sseClient.stream(requestBody, (event) => {
            handleStreamEvent(event);
        });
    } finally {
        uiUpdater.resetButtonState();
        uiUpdater.hideThinkingIndicator();
        stateManager.clearThinkingTimer();
    }
}

/**
 * 스트림 이벤트 처리
 */
function handleStreamEvent(event) {
    // 마지막 이벤트 시간 업데이트
    stateManager.updateLastEventTime();
    
    // "생각중..." 숨기기
    uiUpdater.hideThinkingIndicator();
    
    // 타이머 재시작
    uiUpdater.startThinkingTimer();
    
    // 이벤트 타입별 핸들러 호출
    switch (event.type) {
        case 'thread':
            eventHandlers.handleThreadEvent(event);
            break;
        case 'session':
            eventHandlers.handleSessionEvent(event);
            break;
        case 'scoping_complete':
            eventHandlers.handleScopingCompleteEvent();
            break;
        case 'node_start':
            eventHandlers.handleNodeStartEvent(event);
            break;
        case 'node_complete':
            eventHandlers.handleNodeCompleteEvent(event);
            break;
        case 'research_status':
            eventHandlers.handleResearchStatusEvent(event);
            break;
        case 'research_findings':
            eventHandlers.handleResearchFindingsEvent(event);
            break;
        case 'text_chunk':
            eventHandlers.handleTextChunkEvent(event);
            break;
        case 'final':
            eventHandlers.handleFinalEvent(event);
            break;
        case 'error':
            eventHandlers.handleErrorEvent(event);
            break;
        default:
            console.warn('Unknown event type:', event.type);
    }
}

/**
 * 모바일 메뉴 초기화
 */
function initMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (!menuToggle || !sidebar || !sidebarOverlay) {
        return;
    }
    
    // 햄버거 버튼 클릭
    menuToggle.addEventListener('click', () => {
        const isOpen = sidebar.classList.contains('open');
        
        if (isOpen) {
            closeMobileMenu();
        } else {
            openMobileMenu();
        }
    });
    
    // 오버레이 클릭 시 메뉴 닫기
    sidebarOverlay.addEventListener('click', () => {
        closeMobileMenu();
    });
    
    // Thread 클릭 시 모바일에서 메뉴 닫기 (동적으로 추가된 요소를 위해 이벤트 위임 사용)
    document.addEventListener('click', (e) => {
        if (e.target.closest('.thread-item') && window.innerWidth <= 768) {
            closeMobileMenu();
        }
    });
    
    // 새 대화 버튼 클릭 시 모바일에서 메뉴 닫기
    if (newThreadBtn) {
        newThreadBtn.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                closeMobileMenu();
            }
        });
    }
    
    // 윈도우 리사이즈 시 모바일 메뉴 자동 닫기
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            closeMobileMenu();
        }
    });
}

/**
 * 모바일 메뉴 열기
 */
function openMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (menuToggle) menuToggle.classList.add('active');
    if (sidebar) sidebar.classList.add('open');
    if (sidebarOverlay) sidebarOverlay.classList.add('active');
    document.body.style.overflow = 'hidden'; // 스크롤 방지
}

/**
 * 모바일 메뉴 닫기
 */
function closeMobileMenu() {
    const menuToggle = document.getElementById('menuToggle');
    const sidebar = document.getElementById('sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    
    if (menuToggle) menuToggle.classList.remove('active');
    if (sidebar) sidebar.classList.remove('open');
    if (sidebarOverlay) sidebarOverlay.classList.remove('active');
    document.body.style.overflow = ''; // 스크롤 복원
}
