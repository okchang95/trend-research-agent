// 프로덕션에서는 상대 경로 사용, 개발 환경에서는 절대 경로 사용
const API_URL = window.location.origin + '/agent';
const API_STREAM_URL = window.location.origin + '/agent/stream';

// DOM 요소
const userInput = document.getElementById('userInput');
const searchBtn = document.getElementById('searchBtn');
const responseArea = document.getElementById('responseArea');

// 현재 스트림 상태
let currentEventSource = null;
let finalState = null;

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
    
    // 기존 스트림이 있으면 종료
    if (currentEventSource) {
        currentEventSource.close();
    }
    
    // UI 상태 업데이트
    setLoadingState();
    finalState = null;
    
    try {
        // SSE를 사용한 스트리밍 요청
        await streamAgent(message);
    } catch (error) {
        console.error('Error:', error);
        displayError(error.message);
        resetButtonState();
    }
}

async function streamAgent(message) {
    const response = await fetch(API_STREAM_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_message: message
        })
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
        // 최종 상태 표시
        if (finalState) {
            displayFinalResponse(finalState);
        }
        resetButtonState();
    }
}

function handleStreamEvent(event) {
    if (event.type === 'node_complete') {
        const nodeName = event.node;
        const nodeState = event.state;
        
        // 노드별 상태 업데이트 표시
        updateNodeStatus(nodeName, nodeState);
    } else if (event.type === 'final') {
        finalState = event.state;
    } else if (event.type === 'error') {
        displayError(event.error);
        resetButtonState();
    }
}

function updateNodeStatus(nodeName, nodeState) {
    // 노드 실행 상태를 표시
    let statusText = '';
    
    switch (nodeName) {
        case 'intent_analysis':
            statusText = `🔍 의도 분석 완료: ${nodeState.intent || 'N/A'}`;
            break;
        case 'data_collector':
            statusText = `📚 데이터 수집 완료`;
            break;
        case 'generate_response':
            statusText = `✍️ 응답 생성 완료`;
            break;
        default:
            statusText = `✅ ${nodeName} 완료`;
    }
    
    responseArea.innerHTML = `
        <div class="loading">${statusText}</div>
        <div class="response-content" style="margin-top: 1em; opacity: 0.7;">
            <pre class="json-output"><code>${escapeHtml(JSON.stringify(nodeState, null, 2))}</code></pre>
        </div>
    `;
}

function displayFinalResponse(state) {
    // 최종 응답 표시 (마크다운 렌더링)
    const response = state.response || '';
    
    if (response) {
        // 마크다운을 HTML로 변환
        const html = marked.parse(response);
        responseArea.innerHTML = `
            <div class="response-content">${html}</div>
        `;
    } else {
        // response가 없으면 전체 state를 JSON으로 표시
        const formattedJson = JSON.stringify(state, null, 4);
        responseArea.innerHTML = `
            <pre class="json-output"><code>${escapeHtml(formattedJson)}</code></pre>
        `;
    }
}

function setLoadingState() {
    searchBtn.disabled = true;
    searchBtn.textContent = '검색 중...';
    responseArea.innerHTML = '<p class="loading">응답을 기다리는 중...</p>';
}

function resetButtonState() {
    searchBtn.disabled = false;
    searchBtn.textContent = '검색';
}

function displayResponse(data) {
    // JSON을 예쁘게 포맷팅 (indent=4)
    const formattedJson = JSON.stringify(data, null, 4);
    // JSON을 코드 블록으로 표시
    responseArea.innerHTML = `
        <pre class="json-output"><code>${escapeHtml(formattedJson)}</code></pre>
    `;
}

function displayError(errorMessage) {
    responseArea.innerHTML = `
        <div class="error">
            <strong>오류가 발생했습니다:</strong><br>
            ${escapeHtml(errorMessage)}
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

