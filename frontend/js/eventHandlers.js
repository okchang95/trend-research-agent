/**
 * 이벤트 핸들러 모듈
 * SSE 이벤트 타입별 처리 로직
 */

/**
 * 이벤트 핸들러 클래스
 */
class EventHandlers {
    constructor(stateManager, uiUpdater) {
        this.state = stateManager;
        this.ui = uiUpdater;
    }

    handleSessionEvent(event) {
        this.state.setSessionId(event.session_id);
        console.log('Session ID:', event.session_id);
    }

    handleScopingCompleteEvent() {
        this.state.setScopingComplete(true);
        const messageId = this.state.getCurrentMessageId();
        if (!messageId) {
            return;
        }
        
        const messageElement = document.getElementById(messageId);
        if (!messageElement) {
            return;
        }
        
        const messageText = messageElement.querySelector('.message-text');
        if (!messageText) {
            return;
        }
        
        const currentText = this.state.getText();
        const html = processMarkdownWithMermaid(currentText);
        messageText.innerHTML = html;
        renderMermaidDiagrams(messageText);
    }

    handleNodeStartEvent(event) {
        const nodeName = event.node;
        if (nodeName !== 'clarify_requirement') {
            this.ui.updateNodeStatus(nodeName, null, '진행 중');
        }
    }

    handleNodeCompleteEvent(event) {
        const nodeName = event.node;
        const nodeState = event.state;
        
        if (nodeName !== 'clarify_requirement') {
            this.ui.updateNodeStatus(nodeName, nodeState, '완료');
        }
    }

    handleResearchStatusEvent(event) {
        this.state.clearThinkingTimer();
        this.ui.hideThinkingIndicator();
        this.ui.updateResearchStatus(event.message, event.results);
    }

    handleResearchFindingsEvent(event) {
        this.state.clearThinkingTimer();
        this.ui.hideThinkingIndicator();
        this.ui.displayResearchFindings(event.findings);
    }

    handleTextChunkEvent(event) {
        // scopingComplete 체크 제거: writer 노드의 텍스트 청크도 처리해야 함
        // 백엔드에서 이미 clarify_requirement 노드의 스트리밍은 필터링됨
        
        const messageId = this.state.getCurrentMessageId();
        if (messageId) {
            const messageElement = document.getElementById(messageId);
            if (messageElement) {
                const statusContainer = messageElement.querySelector('.research-status-container');
                if (statusContainer) {
                    statusContainer.style.display = 'none';
                }
            }
        }
        
        this.state.appendText(event.char);
        updateStreamingMessage(messageId, this.state.getText());
    }

    handleFinalEvent(event) {
        this.state.setFinalState(event.state);
        if (event.state && event.state.answer) {
            this.state.setText(event.state.answer);
            updateStreamingMessage(
                this.state.getCurrentMessageId(),
                this.state.getText(),
                true
            );
            this.state.addToHistory('assistant', this.state.getText());
        }
        this.state.setCurrentMessageId(null);
    }

    handleErrorEvent(event) {
        this.ui.displayErrorMessage(event.error);
        this.ui.resetButtonState();
    }
}

