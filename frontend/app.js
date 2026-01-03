/**
 * 메인 애플리케이션 파일
 * 모듈화된 컴포넌트들을 조합하여 애플리케이션 초기화
 */

// API 엔드포인트 설정
const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocalDev ? 'http://localhost:8000' : window.location.origin;
const API_STREAM_URL = API_BASE_URL + '/api/chat/stream';

// DOM 요소
const userInput = document.getElementById('userInput');
const searchBtn = document.getElementById('searchBtn');
const messagesContainer = document.getElementById('messagesContainer');
const introSection = document.getElementById('introSection');
const chatSection = document.getElementById('chatSection');

// 상태 관리 및 모듈 초기화
const stateManager = new StateManager();
const uiUpdater = new UIUpdater(stateManager, messagesContainer);
const eventHandlers = new EventHandlers(stateManager, uiUpdater);
const sseClient = new SSEClient(API_STREAM_URL);

// 현재 스트림 상태
let currentEventSource = null;

// 검색 버튼 클릭 이벤트
searchBtn.addEventListener('click', handleSearch);

// Enter 키 이벤트
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !searchBtn.disabled) {
        handleSearch();
    }
});

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
 * SSE 스트리밍 에이전트 실행
 */
async function streamAgent(message) {
    // 세션 ID가 있으면 사용
    const requestBody = {
        user_message: message
    };
    const sessionId = stateManager.getSessionId();
    if (sessionId) {
        requestBody.session_id = sessionId;
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
