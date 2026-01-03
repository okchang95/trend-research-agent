/**
 * 메시지 렌더링 모듈
 * 메시지 생성 및 업데이트 담당
 */

/**
 * 사용자 메시지 추가
 */
function addUserMessage(message, messagesContainer) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message user-message';
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-text">${escapeHtml(message)}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageElement);
    return messageElement;
}

/**
 * 어시스턴트 메시지 추가
 */
function addAssistantMessage(initialText, messageId, messagesContainer) {
    const messageElement = document.createElement('div');
    messageElement.id = messageId;
    messageElement.className = 'message assistant-message';
    
    const html = initialText ? processMarkdownWithMermaid(initialText) : '';
    
    messageElement.innerHTML = `
        <div class="message-content">
            <div class="message-text">${html}</div>
        </div>
    `;
    
    messagesContainer.appendChild(messageElement);
    
    // Mermaid 렌더링
    if (initialText && typeof mermaid !== 'undefined') {
        renderMermaidDiagrams(messageElement);
    }
    
    return messageElement;
}

/**
 * 스트리밍 메시지 업데이트
 */
function updateStreamingMessage(messageId, text, isFinal = false) {
    const messageElement = document.getElementById(messageId);
    if (!messageElement) return;
    
    const messageText = messageElement.querySelector('.message-text');
    if (!messageText) return;
    
    // 마크다운 및 Mermaid 처리
    const html = processMarkdownWithMermaid(text);
    messageText.innerHTML = html;
    
    // Mermaid 다이어그램 렌더링
    renderMermaidDiagrams(messageText);
    
    // 상태 표시 제거 (최종일 때)
    if (isFinal) {
        const statusDiv = messageElement.querySelector('.node-status');
        if (statusDiv) {
            statusDiv.remove();
        }
        messageElement.classList.add('final');
    }
}

