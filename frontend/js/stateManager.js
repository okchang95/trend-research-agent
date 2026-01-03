/**
 * 상태 관리 모듈
 * 애플리케이션 전역 상태 관리
 */

class StateManager {
    constructor() {
        this.currentSessionId = null;
        this.currentText = '';
        this.conversationHistory = [];
        this.currentMessageId = null;
        this.scopingComplete = false;
        this.lastEventTime = null;
        this.thinkingTimer = null;
        this.finalState = null;
    }

    resetStreamingState() {
        this.currentText = '';
        this.scopingComplete = false;
        this.lastEventTime = Date.now();
        this.finalState = null;
        if (this.thinkingTimer) {
            clearTimeout(this.thinkingTimer);
            this.thinkingTimer = null;
        }
    }

    setSessionId(sessionId) {
        this.currentSessionId = sessionId;
    }

    getSessionId() {
        return this.currentSessionId;
    }

    addToHistory(role, message) {
        this.conversationHistory.push({
            role: role,
            message: message,
            timestamp: new Date()
        });
    }

    getHistory() {
        return this.conversationHistory;
    }

    setCurrentMessageId(messageId) {
        this.currentMessageId = messageId;
    }

    getCurrentMessageId() {
        return this.currentMessageId;
    }

    appendText(text) {
        this.currentText += text;
    }

    setText(text) {
        this.currentText = text;
    }

    getText() {
        return this.currentText;
    }

    setScopingComplete(complete) {
        this.scopingComplete = complete;
    }

    isScopingComplete() {
        return this.scopingComplete;
    }

    updateLastEventTime() {
        this.lastEventTime = Date.now();
    }

    getLastEventTime() {
        return this.lastEventTime;
    }

    setThinkingTimer(timer) {
        if (this.thinkingTimer) {
            clearTimeout(this.thinkingTimer);
        }
        this.thinkingTimer = timer;
    }

    clearThinkingTimer() {
        if (this.thinkingTimer) {
            clearTimeout(this.thinkingTimer);
            this.thinkingTimer = null;
        }
    }

    setFinalState(state) {
        this.finalState = state;
    }

    getFinalState() {
        return this.finalState;
    }
}

