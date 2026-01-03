// API 엔드포인트 설정
// 로컬 개발: localhost:8000, 프로덕션: window.location.origin
const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocalDev ? 'http://localhost:8000' : window.location.origin;

const API_URL = API_BASE_URL + '/api/chat';
const API_STREAM_URL = API_BASE_URL + '/api/chat/stream';

// DOM 요소
const userInput = document.getElementById('userInput');
const searchBtn = document.getElementById('searchBtn');
const messagesContainer = document.getElementById('messagesContainer');
const introSection = document.getElementById('introSection');
const chatSection = document.getElementById('chatSection');

// 현재 스트림 상태
let currentEventSource = null;
let finalState = null;
let currentSessionId = null;
let currentText = ''; // 스트리밍 중인 텍스트
let conversationHistory = []; // 대화 히스토리
let currentMessageId = null; // 현재 스트리밍 중인 메시지 ID
let scopingComplete = false; // clarify_requirement의 answer 스트리밍 완료 여부
let lastEventTime = null; // 마지막 이벤트 발생 시간
let thinkingTimer = null; // "생각중..." 표시 타이머

// 검색 버튼 클릭 이벤트
searchBtn.addEventListener('click', handleSearch);

// Enter 키 이벤트
userInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !searchBtn.disabled) {
        handleSearch();
    }
});

async function handleSearch() {
    const message = userInput.value.trim();
    
    if (!message) {
        alert('메시지를 입력해주세요.');
        return;
    }
    
    // 첫 대화인 경우 소개 섹션 숨기고 대화창 표시
    if (conversationHistory.length === 0) {
        introSection.style.display = 'none';
        chatSection.style.display = 'block';
    }
    
    // 기존 스트림이 있으면 종료
    if (currentEventSource) {
        currentEventSource.close();
    }
    
    // 사용자 메시지 추가
    const userMessageElement = addUserMessage(message);
    
    // 입력 필드 초기화
    userInput.value = '';
    
    // UI 상태 업데이트
    setLoadingState();
    finalState = null;
    currentText = ''; // 텍스트 초기화
    scopingComplete = false; // scoping 완료 플래그 초기화
    lastEventTime = Date.now(); // 마지막 이벤트 시간 초기화
    
    // 기존 타이머 정리
    if (thinkingTimer) {
        clearTimeout(thinkingTimer);
        thinkingTimer = null;
    }
    
    // 어시스턴트 메시지 영역 생성
    currentMessageId = 'msg-' + Date.now();
    addAssistantMessage('', currentMessageId);
    
    // "생각중..." 표시를 위한 타이머 시작
    startThinkingTimer();
    
    // 사용자 메시지 추가 후 해당 메시지로 스크롤
    setTimeout(() => {
        scrollToMessage(userMessageElement);
    }, 100);
    
    try {
        // SSE를 사용한 스트리밍 요청
        await streamAgent(message);
    } catch (error) {
        console.error('Error:', error);
        displayErrorMessage(error.message);
        resetButtonState();
    }
}

async function streamAgent(message) {
    // 세션 ID가 있으면 사용, 없으면 null
    const requestBody = {
        user_message: message
    };
    if (currentSessionId) {
        requestBody.session_id = currentSessionId;
    }
    
    const response = await fetch(API_STREAM_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    try {
        while (true) {
            const { done, value } = await reader.read();
            
            if (done) {
                break;
            }
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // 마지막 불완전한 라인은 버퍼에 보관
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6); // 'data: ' 제거
                    try {
                        const event = JSON.parse(data);
                        handleStreamEvent(event);
                    } catch (e) {
                        console.error('Failed to parse SSE data:', e);
                    }
                }
            }
        }
        
        // 버퍼에 남은 데이터 처리
        if (buffer.startsWith('data: ')) {
            const data = buffer.slice(6);
            try {
                const event = JSON.parse(data);
                handleStreamEvent(event);
            } catch (e) {
                console.error('Failed to parse SSE buffer:', e);
            }
        }
        
    } finally {
        reader.releaseLock();
        resetButtonState();
        // 스트리밍 종료 시 "생각중..." 숨기기
        hideThinkingIndicator();
        if (thinkingTimer) {
            clearTimeout(thinkingTimer);
            thinkingTimer = null;
        }
    }
}

function handleStreamEvent(event) {
    // 마지막 이벤트 시간 업데이트
    lastEventTime = Date.now();
    
    // "생각중..." 숨기기
    hideThinkingIndicator();
    
    // 타이머 재시작
    startThinkingTimer();
    
    if (event.type === 'session') {
        // 세션 ID 저장
        currentSessionId = event.session_id;
        console.log('Session ID:', currentSessionId);
    } else if (event.type === 'scoping_complete') {
        // clarify_requirement 노드의 answer 스트리밍이 완료되었음을 표시
        // 이 시점에서 스트리밍을 완료하고 researcher 노드 시작을 기다림
        scopingComplete = true;
        if (currentMessageId) {
            const messageElement = document.getElementById(currentMessageId);
            if (messageElement) {
                const messageText = messageElement.querySelector('.message-text');
                if (messageText) {
                    // Mermaid 코드 블록을 먼저 처리 (마크다운 파싱 전)
                    let processedText = currentText;
                    const mermaidPlaceholders = [];
                    
                    if (typeof mermaid !== 'undefined') {
                        const mermaidRegex = /```mermaid\s*\n([\s\S]*?)```/g;
                        let match;
                        let index = 0;
                        while ((match = mermaidRegex.exec(currentText)) !== null) {
                            const placeholder = `__MERMAID_PLACEHOLDER_${index}__`;
                            mermaidPlaceholders.push({
                                placeholder: placeholder,
                                content: match[1].trim()
                            });
                            processedText = processedText.replace(match[0], placeholder);
                            index++;
                        }
                    }
                    
                    // 마크다운을 HTML로 변환
                    let html = marked.parse(processedText);
                    
                    // 플레이스홀더를 실제 Mermaid div로 교체
                    if (typeof mermaid !== 'undefined' && mermaidPlaceholders.length > 0) {
                        mermaidPlaceholders.forEach((item) => {
                            const mermaidDiv = `<div class="mermaid">${item.content}</div>`;
                            html = html.replace(item.placeholder, mermaidDiv);
                        });
                    }
                    
                    messageText.innerHTML = html;
                    
                    // Mermaid 렌더링 (있는 경우)
                    if (typeof mermaid !== 'undefined') {
                        try {
                            mermaid.initialize({ startOnLoad: false, theme: 'default' });
                            const mermaidDiagrams = messageText.querySelectorAll('.mermaid');
                            mermaidDiagrams.forEach((diagram) => {
                                if (!diagram.hasAttribute('data-processed')) {
                                    mermaid.run({ nodes: [diagram] });
                                }
                            });
                        } catch (e) {
                            console.error('Mermaid rendering error:', e);
                        }
                    }
                }
            }
        }
        // scoping_complete 후에는 더 이상 text_chunk를 처리하지 않음
        // researcher 노드가 시작되면 그때부터 새로운 스트리밍 시작
    } else if (event.type === 'node_start') {
        // 노드 시작 이벤트 - "진행 중" 상태 표시 (clarify_requirement 제외)
        const nodeName = event.node;
        // 일반 대화에서는 요구사항 명확화 진행 상태를 표시하지 않음
        if (nodeName !== 'clarify_requirement') {
            updateNodeStatus(nodeName, null, '진행 중');
        }
    } else if (event.type === 'node_complete') {
        // 노드 완료 이벤트
        const nodeName = event.node;
        const nodeState = event.state;
        
        // 노드별 상태 업데이트 표시 (완료 상태, clarify_requirement 제외)
        if (nodeName !== 'clarify_requirement') {
            updateNodeStatus(nodeName, nodeState, '완료');
        }
    } else if (event.type === 'research_status') {
        // 조사 상태 메시지 업데이트 (한 줄로 동적 업데이트)
        updateResearchStatus(event.message, event.results);
    } else if (event.type === 'research_findings') {
        // 조사 내용을 토글 형태로 표시
        displayResearchFindings(event.findings);
    } else if (event.type === 'text_chunk') {
        // scoping_complete가 true이면 clarify_requirement의 answer 스트리밍을 중단
        if (scopingComplete) {
            return; // 더 이상 text_chunk를 처리하지 않음
        }
        // writer 노드의 텍스트 스트리밍이 시작되면 research_status 컨테이너 숨기기
        if (currentMessageId) {
            const messageElement = document.getElementById(currentMessageId);
            if (messageElement) {
                const statusContainer = messageElement.querySelector('.research-status-container');
                if (statusContainer) {
                    statusContainer.style.display = 'none';
                }
            }
        }
        // 글자 단위 스트리밍
        currentText += event.char;
        updateStreamingMessage(currentMessageId, currentText);
        // 스트리밍 중 자동 스크롤은 MutationObserver가 처리
    } else if (event.type === 'final') {
        finalState = event.state;
        // 최종 텍스트가 있으면 표시
        if (event.state && event.state.answer) {
            currentText = event.state.answer;
            updateStreamingMessage(currentMessageId, currentText, true);
            // 대화 히스토리에 추가
            conversationHistory.push({
                role: 'assistant',
                message: currentText,
                timestamp: new Date()
            });
        }
        currentMessageId = null;
    } else if (event.type === 'error') {
        displayErrorMessage(event.error);
        resetButtonState();
    }
}

function updateNodeStatus(nodeName, nodeState, status = '완료') {
    // 노드 실행 상태를 현재 메시지에 표시
    if (!currentMessageId) return;
    
    const messageElement = document.getElementById(currentMessageId);
    if (!messageElement) return;
    
    let statusText = '';
    let statusIcon = '';
    
    // 상태에 따라 아이콘과 텍스트 설정 (간결하게)
    if (status === '진행 중') {
        switch (nodeName) {
            case 'clarify_requirement':
                statusIcon = '🔍';
                statusText = '요구사항 명확화 중...';
                break;
            case 'researcher':
                statusIcon = '📚';
                statusText = '자료 수집 중...';
                break;
            case 'writer':
                statusIcon = '✍️';
                statusText = '보고서 작성 중...';
                break;
            default:
                statusIcon = '⏳';
                statusText = `${nodeName} 진행 중...`;
        }
    } else if (status === '완료') {
    switch (nodeName) {
            case 'clarify_requirement':
                statusIcon = '✅';
                statusText = '명확화 완료';
            break;
            case 'researcher':
                statusIcon = '✅';
                statusText = `수집 완료 (${nodeState?.findings_count || 0}개)`;
            break;
            case 'writer':
                statusIcon = '✅';
                statusText = '작성 완료';
            break;
        default:
                statusIcon = '✅';
                statusText = `${nodeName} 완료`;
        }
    }
    
    // 상태 표시 업데이트
    let statusDiv = messageElement.querySelector('.node-status');
    if (!statusDiv) {
        statusDiv = document.createElement('div');
        statusDiv.className = 'node-status';
        const messageContent = messageElement.querySelector('.message-content');
        if (messageContent) {
            messageContent.insertBefore(statusDiv, messageContent.firstChild);
        }
    }
    
    // 진행 중일 때는 애니메이션 추가
    if (status === '진행 중') {
        statusDiv.innerHTML = `<div class="loading progress">${statusIcon} ${statusText}</div>`;
        statusDiv.classList.add('progressing');
    } else {
        statusDiv.innerHTML = `<div class="loading">${statusIcon} ${statusText}</div>`;
        statusDiv.classList.remove('progressing');
    }
}

function addUserMessage(message) {
    // 대화 히스토리에 추가
    conversationHistory.push({
        role: 'user',
        message: message,
        timestamp: new Date()
    });
    
    // 메시지 요소 생성
    const messageElement = document.createElement('div');
    messageElement.className = 'message user-message';
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-text">${escapeHtml(message)}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageElement);
    
    // 해당 메시지로 스크롤 (최상단으로)
    return messageElement;
}

function addAssistantMessage(initialText, messageId) {
    // 메시지 요소 생성
    const messageElement = document.createElement('div');
    messageElement.id = messageId;
    messageElement.className = 'message assistant-message';
    
    // Mermaid 코드 블록을 먼저 처리 (마크다운 파싱 전)
    let processedText = initialText || '';
    const mermaidPlaceholders = [];
    
    if (processedText && typeof mermaid !== 'undefined') {
        // mermaid 코드 블록을 찾아서 플레이스홀더로 교체
        const mermaidRegex = /```mermaid\s*\n([\s\S]*?)```/g;
        let match;
        let index = 0;
        while ((match = mermaidRegex.exec(initialText)) !== null) {
            const placeholder = `__MERMAID_PLACEHOLDER_${index}__`;
            mermaidPlaceholders.push({
                placeholder: placeholder,
                content: match[1].trim()
            });
            processedText = processedText.replace(match[0], placeholder);
            index++;
        }
    }
    
        // 마크다운을 HTML로 변환
    let html = processedText ? marked.parse(processedText) : '';
    
    // 플레이스홀더를 실제 Mermaid div로 교체
    if (typeof mermaid !== 'undefined' && mermaidPlaceholders.length > 0) {
        mermaidPlaceholders.forEach((item) => {
            const mermaidDiv = `<div class="mermaid">${item.content}</div>`;
            html = html.replace(item.placeholder, mermaidDiv);
        });
    }
    
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-text">${html}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageElement);
    
    // Mermaid 렌더링
    if (initialText && typeof mermaid !== 'undefined') {
        try {
            mermaid.initialize({ startOnLoad: false, theme: 'default' });
            const mermaidDiagrams = messageElement.querySelectorAll('.mermaid');
            mermaidDiagrams.forEach((diagram) => {
                if (!diagram.hasAttribute('data-processed')) {
                    mermaid.run({ nodes: [diagram] });
                }
            });
        } catch (e) {
            console.error('Mermaid rendering error:', e);
        }
    }
    
    return messageElement;
}

function updateStreamingMessage(messageId, text, isFinal = false) {
    const messageElement = document.getElementById(messageId);
    if (!messageElement) return;
    
    const messageText = messageElement.querySelector('.message-text');
    if (!messageText) return;
    
    // Mermaid 코드 블록을 먼저 처리 (마크다운 파싱 전)
    let processedText = text;
    const mermaidPlaceholders = [];
    
    if (typeof mermaid !== 'undefined') {
        // mermaid 코드 블록을 찾아서 플레이스홀더로 교체
        const mermaidRegex = /```mermaid\s*\n([\s\S]*?)```/g;
        let match;
        let index = 0;
        while ((match = mermaidRegex.exec(text)) !== null) {
            const placeholder = `__MERMAID_PLACEHOLDER_${index}__`;
            mermaidPlaceholders.push({
                placeholder: placeholder,
                content: match[1].trim()
            });
            processedText = processedText.replace(match[0], placeholder);
            index++;
        }
    }
    
    // 마크다운을 HTML로 변환
    let html = marked.parse(processedText);
    
    // 플레이스홀더를 실제 Mermaid div로 교체
    if (typeof mermaid !== 'undefined' && mermaidPlaceholders.length > 0) {
        mermaidPlaceholders.forEach((item) => {
            const mermaidDiv = `<div class="mermaid">${item.content}</div>`;
            html = html.replace(item.placeholder, mermaidDiv);
        });
    }
    
    messageText.innerHTML = html;
    
    // Mermaid 다이어그램 렌더링
    if (typeof mermaid !== 'undefined') {
        try {
            mermaid.initialize({ startOnLoad: false, theme: 'default' });
            const mermaidDiagrams = messageText.querySelectorAll('.mermaid');
            mermaidDiagrams.forEach((diagram) => {
                if (!diagram.hasAttribute('data-processed')) {
                    mermaid.run({ nodes: [diagram] });
                }
            });
        } catch (e) {
            console.error('Mermaid rendering error:', e);
        }
    }
    
    // 상태 표시 제거 (최종일 때)
    if (isFinal) {
        const statusDiv = messageElement.querySelector('.node-status');
        if (statusDiv) {
            statusDiv.remove();
        }
        messageElement.classList.add('final');
    }
    
}

function setLoadingState() {
    searchBtn.disabled = true;
    searchBtn.textContent = '검색 중...';
    currentText = ''; // 텍스트 초기화
}

function resetButtonState() {
    searchBtn.disabled = false;
    searchBtn.textContent = '검색';
}

function displayErrorMessage(errorMessage) {
    // 에러 메시지를 어시스턴트 메시지로 표시
    if (currentMessageId) {
        const messageElement = document.getElementById(currentMessageId);
        if (messageElement) {
            const messageText = messageElement.querySelector('.message-text');
            if (messageText) {
                messageText.innerHTML = `
        <div class="error">
            <strong>오류가 발생했습니다:</strong><br>
            ${escapeHtml(errorMessage)}
        </div>
    `;
            }
        }
    } else {
        // 메시지 ID가 없으면 새로 생성
        addAssistantMessage('', 'error-' + Date.now());
        updateStreamingMessage('error-' + Date.now(), `
            <div class="error">
                <strong>오류가 발생했습니다:</strong><br>
                ${escapeHtml(errorMessage)}
            </div>
        `, true);
    }
    resetButtonState();
}

function updateResearchStatus(message, results = null) {
    // researcher 노드가 실행 중일 때만 상태 메시지 업데이트
    if (!currentMessageId) return;
    
    const messageElement = document.getElementById(currentMessageId);
    if (!messageElement) return;
    
    // 조사 상태 컨테이너 찾기 또는 생성
    let statusContainer = messageElement.querySelector('.research-status-container');
    if (!statusContainer) {
        statusContainer = document.createElement('div');
        statusContainer.className = 'research-status-container';
        const messageContent = messageElement.querySelector('.message-content');
        if (messageContent) {
            // node-status 다음에 삽입
            const nodeStatus = messageContent.querySelector('.node-status');
            if (nodeStatus) {
                nodeStatus.insertAdjacentElement('afterend', statusContainer);
            } else {
                messageContent.insertBefore(statusContainer, messageContent.firstChild);
            }
        }
    }
    
    // 상태 메시지와 결과 표시
    let html = `<div class="research-status-message">${escapeHtml(message)}</div>`;
    
    // 검색 결과가 있으면 링크와 스니펫 표시
    if (results && Array.isArray(results) && results.length > 0) {
        html += '<div class="research-results-preview">';
        results.forEach((result, index) => {
            const title = result.title || '제목 없음';
            const url = result.url || '';
            const snippet = result.snippet || '';
            
            html += `<div class="result-preview-item">`;
            if (url) {
                html += `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="result-preview-link">${escapeHtml(title)}</a>`;
            } else {
                html += `<span class="result-preview-title">${escapeHtml(title)}</span>`;
            }
            if (snippet) {
                html += `<div class="result-preview-snippet">${escapeHtml(snippet)}</div>`;
            }
            html += `</div>`;
        });
        html += '</div>';
    }
    
    statusContainer.innerHTML = html;
}

function displayResearchFindings(findings) {
    // researcher 노드가 실행 중일 때만 findings 표시
    if (!currentMessageId) return;
    
    const messageElement = document.getElementById(currentMessageId);
    if (!messageElement) return;
    
    // findings 컨테이너 찾기 또는 생성
    let findingsContainer = messageElement.querySelector('.research-findings-container');
    if (!findingsContainer) {
        findingsContainer = document.createElement('div');
        findingsContainer.className = 'research-findings-container';
        const messageContent = messageElement.querySelector('.message-content');
        if (messageContent) {
            // node-status 다음에 삽입
            const nodeStatus = messageContent.querySelector('.node-status');
            if (nodeStatus) {
                nodeStatus.insertAdjacentElement('afterend', findingsContainer);
            } else {
                messageContent.insertBefore(findingsContainer, messageContent.firstChild);
            }
        }
    }
    
    // findings HTML 생성 (토글 형태)
    let findingsHTML = '<div class="research-findings-header">';
    findingsHTML += '<button class="research-findings-toggle" onclick="toggleResearchFindings(this)">';
    findingsHTML += '<span class="toggle-icon">▼</span> ';
    findingsHTML += '<span class="toggle-text">조사 내용 보기</span>';
    findingsHTML += ` <span class="findings-count">(${findings.length}개)</span>`;
    findingsHTML += '</button>';
    findingsHTML += '</div>';
    findingsHTML += '<div class="research-findings-content" style="display: none;">';
    
    findings.forEach((finding, index) => {
        // finding이 딕셔너리인지 확인
        const findingType = finding.type || finding['type'] || '';
        if (findingType === 'final_summary') {
            // 최종 요약은 별도로 표시
            const summary = finding.summary || finding['summary'] || '';
            findingsHTML += `<div class="finding-item finding-summary">
                <div class="finding-header">📝 최종 요약</div>
                <div class="finding-content">${escapeHtml(summary)}</div>
            </div>`;
        } else {
            const query = finding.query || finding['query'] || '';
            const results = finding.results || finding['results'] || [];
            const toolType = finding.tool_type || finding['tool_type'] || 'web_search';
            const iteration = finding.iteration || finding['iteration'] || index + 1;
            
            findingsHTML += `<div class="finding-item">
                <div class="finding-header">
                    <span class="finding-number">${iteration}</span>
                    <span class="finding-query">${escapeHtml(query)}</span>
                    <span class="finding-tool-type">${toolType === 'web_search' ? '🌐' : '📄'}</span>
                </div>
                <div class="finding-content">`;
            
            if (Array.isArray(results)) {
                results.forEach((result, resultIndex) => {
                    if (typeof result === 'object' && result !== null) {
                        const title = result.title || result['title'] || '제목 없음';
                        const url = result.url || result['url'] || '';
                        const content = result.content || result['content'] || '';
                        const contentPreview = content.length > 200 ? content.substring(0, 200) + '...' : content;
                        
                        findingsHTML += `<div class="finding-result">
                            <div class="result-title">${escapeHtml(title)}</div>
                            ${url ? `<div class="result-url"><a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(url)}</a></div>` : ''}
                            ${contentPreview ? `<div class="result-content">${escapeHtml(contentPreview)}</div>` : ''}
                        </div>`;
                    } else {
                        findingsHTML += `<div class="finding-result">${escapeHtml(String(result))}</div>`;
                    }
                });
            } else {
                findingsHTML += `<div class="finding-result">${escapeHtml(String(results))}</div>`;
            }
            
            findingsHTML += '</div></div>';
        }
    });
    
    findingsHTML += '</div>';
    
    findingsContainer.innerHTML = findingsHTML;
}

function toggleResearchFindings(button) {
    const container = button.closest('.research-findings-container');
    const content = container.querySelector('.research-findings-content');
    const icon = button.querySelector('.toggle-icon');
    const text = button.querySelector('.toggle-text');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        icon.textContent = '▲';
        text.textContent = '조사 내용 숨기기';
    } else {
        content.style.display = 'none';
        icon.textContent = '▼';
        text.textContent = '조사 내용 보기';
    }
}

function scrollToMessage(messageElement) {
    if (!messageElement) return;
    
    // 메시지 요소의 위치로 스크롤 (최상단에 위치하도록)
    requestAnimationFrame(() => {
        const elementTop = messageElement.getBoundingClientRect().top + window.pageYOffset;
        const offset = 100; // 상단 여백
        window.scrollTo({
            top: elementTop - offset,
            behavior: 'smooth'
        });
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// "생각중..." 표시 함수
function startThinkingTimer() {
    // 기존 타이머 정리
    if (thinkingTimer) {
        clearTimeout(thinkingTimer);
    }
    
    // 1.5초 후에도 이벤트가 없으면 "생각중..." 표시
    thinkingTimer = setTimeout(() => {
        if (currentMessageId && !scopingComplete) {
            showThinkingIndicator();
        }
    }, 1500);
}

function showThinkingIndicator() {
    if (!currentMessageId) return;
    
    const messageElement = document.getElementById(currentMessageId);
    if (!messageElement) return;
    
    // 이미 표시되어 있으면 중복 생성 방지
    let thinkingDiv = messageElement.querySelector('.thinking-indicator');
    if (thinkingDiv) return;
    
    const messageContent = messageElement.querySelector('.message-content');
    if (!messageContent) return;
    
    const messageText = messageContent.querySelector('.message-text');
    if (!messageText) return;
    
    thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'thinking-indicator';
    thinkingDiv.textContent = '생각중...';
    
    // 메시지 텍스트 다음에 추가
    messageText.appendChild(thinkingDiv);
}

function hideThinkingIndicator() {
    if (!currentMessageId) return;
    
    const messageElement = document.getElementById(currentMessageId);
    if (!messageElement) return;
    
    const thinkingDiv = messageElement.querySelector('.thinking-indicator');
    if (thinkingDiv) {
        thinkingDiv.remove();
    }
}

