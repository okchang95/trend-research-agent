/**
 * UI 업데이트 모듈
 * UI 상태 업데이트 및 표시 로직
 */

/**
 * UI 업데이트 클래스
 */
class UIUpdater {
    constructor(stateManager, messagesContainer) {
        this.state = stateManager;
        this.messagesContainer = messagesContainer;
        this.searchBtn = document.getElementById('searchBtn');
        this.userInput = document.getElementById('userInput');
        this.introSection = document.getElementById('introSection');
        this.chatSection = document.getElementById('chatSection');
    }

    setLoadingState() {
        this.searchBtn.disabled = true;
        this.searchBtn.textContent = '검색 중...';
        this.state.setText('');
    }

    resetButtonState() {
        this.searchBtn.disabled = false;
        this.searchBtn.textContent = '검색';
    }

    displayErrorMessage(errorMessage) {
        const messageId = this.state.getCurrentMessageId();
        if (messageId) {
            const messageElement = document.getElementById(messageId);
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
            const newMessageId = 'error-' + Date.now();
            addAssistantMessage('', newMessageId, this.messagesContainer);
            updateStreamingMessage(newMessageId, `
                <div class="error">
                    <strong>오류가 발생했습니다:</strong><br>
                    ${escapeHtml(errorMessage)}
                </div>
            `, true);
        }
        this.resetButtonState();
    }

    updateNodeStatus(nodeName, nodeState, status = '완료') {
        const messageId = this.state.getCurrentMessageId();
        if (!messageId) return;
        
        const messageElement = document.getElementById(messageId);
        if (!messageElement) return;
        
        let statusText = '';
        let statusIcon = '';
        
        // 상태에 따라 아이콘과 텍스트 설정
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
                    // 수집 완료 표시 제거
                    return;
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

    updateResearchStatus(message, results = null) {
        const messageId = this.state.getCurrentMessageId();
        if (!messageId) return;
        
        const messageElement = document.getElementById(messageId);
        if (!messageElement) return;
        
        // 조사 상태 컨테이너 찾기 또는 생성
        let statusContainer = messageElement.querySelector('.research-status-container');
        if (!statusContainer) {
            statusContainer = document.createElement('div');
            statusContainer.className = 'research-status-container';
            const messageContent = messageElement.querySelector('.message-content');
            if (messageContent) {
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
            results.forEach((result) => {
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

    displayResearchFindings(findings) {
        const messageId = this.state.getCurrentMessageId();
        if (!messageId) return;
        
        const messageElement = document.getElementById(messageId);
        if (!messageElement) return;
        
        // findings 컨테이너 찾기 또는 생성
        let findingsContainer = messageElement.querySelector('.research-findings-container');
        if (!findingsContainer) {
            findingsContainer = document.createElement('div');
            findingsContainer.className = 'research-findings-container';
            const messageContent = messageElement.querySelector('.message-content');
            if (messageContent) {
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
            const findingType = finding.type || finding['type'] || '';
            if (findingType === 'final_summary') {
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
                    results.forEach((result) => {
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

    startThinkingTimer() {
        this.state.clearThinkingTimer();
        
        const timer = setTimeout(() => {
            const messageId = this.state.getCurrentMessageId();
            if (messageId && !this.state.isScopingComplete()) {
                this.showThinkingIndicator();
            }
        }, 1500);
        
        this.state.setThinkingTimer(timer);
    }

    showThinkingIndicator() {
        const messageId = this.state.getCurrentMessageId();
        if (!messageId) return;
        
        const messageElement = document.getElementById(messageId);
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
        
        messageText.appendChild(thinkingDiv);
    }

    hideThinkingIndicator() {
        const messageId = this.state.getCurrentMessageId();
        if (!messageId) return;
        
        const messageElement = document.getElementById(messageId);
        if (!messageElement) return;
        
        const thinkingDiv = messageElement.querySelector('.thinking-indicator');
        if (thinkingDiv) {
            thinkingDiv.remove();
        }
    }

    scrollToMessage(messageElement) {
        if (!messageElement) return;
        
        requestAnimationFrame(() => {
            const elementTop = messageElement.getBoundingClientRect().top + window.pageYOffset;
            const offset = 100;
            window.scrollTo({
                top: elementTop - offset,
                behavior: 'smooth'
            });
        });
    }
}

// 전역 함수 (HTML에서 호출)
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

