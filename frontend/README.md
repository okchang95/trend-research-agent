# Frontend - AI 트렌드 분석 어시스턴트

Vanilla JavaScript로 구현된 모듈화된 프론트엔드 애플리케이션입니다. SSE(Server-Sent Events)를 통한 실시간 스트리밍과 마크다운/Mermaid 다이어그램 렌더링을 지원합니다.

## 🛠 기술 스택

- **Vanilla JavaScript**: 순수 JavaScript (프레임워크 없음)
- **Marked.js**: 마크다운 파싱
- **Mermaid.js**: 다이어그램 렌더링
- **SSE (Server-Sent Events)**: 실시간 스트리밍 통신
- **HTML5/CSS3**: 모던 웹 표준

## 📁 프로젝트 구조

```
frontend/
├── js/
│   ├── sseClient.js        # SSE 클라이언트
│   ├── stateManager.js      # 상태 관리
│   ├── eventHandlers.js     # 이벤트 핸들러
│   ├── uiUpdater.js         # UI 업데이트
│   ├── messageRenderer.js   # 메시지 렌더링
│   └── markdownUtils.js    # 마크다운/Mermaid 유틸리티
├── app.js                   # 메인 애플리케이션
├── index.html              # HTML 템플릿
├── styles.css              # 스타일시트
└── serve.sh                # 개발 서버 스크립트
```

## 🚀 설치 및 실행

### 로컬 개발 서버

#### Python HTTP 서버

```bash
# Python 3
python -m http.server 8080

# Python 2
python -m SimpleHTTPServer 8080
```

#### serve.sh 스크립트 사용

```bash
chmod +x serve.sh
./serve.sh
```

#### Node.js http-server (선택사항)

```bash
npx http-server -p 8080
```

### Docker/Nginx로 실행

프로덕션 환경에서는 Nginx를 통해 서빙됩니다:

```bash
docker-compose up nginx
```

## 🏗 모듈 구조

### 메인 애플리케이션 (`app.js`)

애플리케이션 초기화 및 이벤트 흐름 관리:

- API 엔드포인트 설정
- 모듈 초기화 (StateManager, UIUpdater, EventHandlers, SSEClient)
- 검색 버튼 및 Enter 키 이벤트 처리
- SSE 스트리밍 요청 처리

**주요 함수:**
- `handleSearch()`: 검색 요청 처리
- `streamAgent()`: SSE 스트리밍 에이전트 실행
- `handleStreamEvent()`: 스트림 이벤트 라우팅

### SSE 클라이언트 (`js/sseClient.js`)

SSE 연결 및 파싱을 담당합니다.

```javascript
const sseClient = new SSEClient(API_STREAM_URL);
await sseClient.stream(requestBody, (event) => {
    handleStreamEvent(event);
});
```

**주요 기능:**
- SSE 연결 관리
- 이벤트 파싱
- 에러 처리
- 연결 종료 처리

### 상태 관리 (`js/stateManager.js`)

애플리케이션 전역 상태를 관리합니다.

```javascript
const stateManager = new StateManager();
stateManager.setSessionId(sessionId);
stateManager.appendText(text);
```

**주요 상태:**
- `currentSessionId`: 현재 세션 ID
- `currentText`: 스트리밍 중인 텍스트
- `conversationHistory`: 대화 히스토리
- `currentMessageId`: 현재 메시지 ID
- `scopingComplete`: 요구사항 명확화 완료 여부
- `finalState`: 최종 상태

**주요 메서드:**
- `resetStreamingState()`: 스트리밍 상태 초기화
- `setSessionId()` / `getSessionId()`: 세션 ID 관리
- `addToHistory()`: 대화 히스토리 추가
- `appendText()` / `getText()`: 텍스트 관리

### 이벤트 핸들러 (`js/eventHandlers.js`)

SSE 이벤트 타입별 처리 로직을 담당합니다.

**지원 이벤트 타입:**
- `session`: 세션 ID 수신
- `scoping_complete`: 요구사항 명확화 완료
- `node_start`: 노드 시작
- `node_complete`: 노드 완료 (writer 노드 완료 시 검색창 비활성화)
- `research_status`: 조사 상태 업데이트
- `research_findings`: 조사 결과
- `text_chunk`: 텍스트 청크 (스트리밍)
- `final`: 최종 결과
- `error`: 에러

**주요 메서드:**
- `handleSessionEvent()`: 세션 ID 처리
- `handleScopingCompleteEvent()`: 요구사항 명확화 완료 처리
- `handleNodeCompleteEvent()`: 노드 완료 처리 (writer 노드 완료 시 검색창 비활성화)
- `handleTextChunkEvent()`: 텍스트 청크 스트리밍 처리
- `handleFinalEvent()`: 최종 결과 처리

### UI 업데이트 (`js/uiUpdater.js`)

UI 상태 업데이트 및 표시를 담당합니다.

**주요 기능:**
- 노드 상태 표시 (진행 중/완료)
- 조사 상태 및 결과 표시
- 에러 메시지 표시
- "생각중..." 인디케이터
- 스크롤 관리
- 보고서 작성 완료 시 검색창 비활성화

**주요 메서드:**
- `setLoadingState()`: 로딩 상태 설정
- `resetButtonState()`: 버튼 상태 초기화
- `updateNodeStatus()`: 노드 상태 업데이트
- `updateResearchStatus()`: 조사 상태 업데이트
- `displayResearchFindings()`: 조사 결과 표시
- `disableInput()`: 검색창 비활성화 (보고서 완료 시)

### 메시지 렌더링 (`js/messageRenderer.js`)

메시지 생성 및 업데이트를 담당합니다.

```javascript
// 사용자 메시지 추가
addUserMessage(message, messagesContainer);

// 어시스턴트 메시지 추가
addAssistantMessage(initialText, messageId, messagesContainer);

// 스트리밍 메시지 업데이트
updateStreamingMessage(messageId, text, isFinal);
```

**주요 함수:**
- `addUserMessage()`: 사용자 메시지 DOM 요소 생성
- `addAssistantMessage()`: 어시스턴트 메시지 DOM 요소 생성
- `updateStreamingMessage()`: 스트리밍 중인 메시지 업데이트

### 마크다운 유틸리티 (`js/markdownUtils.js`)

마크다운 파싱 및 Mermaid 다이어그램 처리를 담당합니다.

```javascript
// 마크다운 및 Mermaid 처리
const html = processMarkdownWithMermaid(text);

// Mermaid 다이어그램 렌더링
renderMermaidDiagrams(container);
```

**주요 함수:**
- `safeMarkdownParse()`: 안전한 마크다운 파싱
- `processMermaidBlocks()`: Mermaid 코드 블록 처리
- `renderMermaidDiagrams()`: Mermaid 다이어그램 렌더링
- `processMarkdownWithMermaid()`: 통합 처리
- `escapeHtml()`: HTML 이스케이프

## 🎨 UI 기능

### 실시간 스트리밍

- SSE를 통한 실시간 텍스트 스트리밍
- 노드별 진행 상황 표시
- 조사 상태 및 결과 실시간 업데이트

### 마크다운 지원

- 마크다운 문법 지원
- 코드 블록 하이라이팅
- 링크, 리스트, 테이블 등 지원

### Mermaid 다이어그램

- Mermaid 코드 블록 자동 렌더링
- 플로우차트, 시퀀스 다이어그램 등 지원
- 지연 렌더링으로 성능 최적화

### 조사 결과 표시

- 토글 가능한 조사 내용 섹션
- 검색 결과 미리보기 (링크 및 스니펫)
- 논문 및 웹 검색 결과 구분 표시

### 보고서 완료 처리

- writer 노드 완료 시 검색창 및 전송 버튼 자동 비활성화
- 보고서 작성 완료 후 추가 입력 방지

## 🔧 개발 가이드

### 새로운 이벤트 타입 추가

1. `js/eventHandlers.js`의 `EventHandlers` 클래스에 새 메서드 추가:

```javascript
handleNewEventType(event) {
    // 이벤트 처리 로직
    this.ui.updateSomething(event.data);
}
```

2. `app.js`의 `handleStreamEvent()` 함수에 케이스 추가:

```javascript
case 'new_event_type':
    eventHandlers.handleNewEventType(event);
    break;
```

### UI 컴포넌트 추가

`js/uiUpdater.js`의 `UIUpdater` 클래스에 새 메서드 추가:

```javascript
updateNewComponent(data) {
    const messageId = this.state.getCurrentMessageId();
    // UI 업데이트 로직
}
```

### 스타일 수정

`styles.css` 파일을 수정하여 스타일을 변경할 수 있습니다.

주요 CSS 클래스:
- `.message`: 메시지 컨테이너
- `.user-message`: 사용자 메시지
- `.assistant-message`: 어시스턴트 메시지
- `.node-status`: 노드 상태 표시
- `.research-status-container`: 조사 상태 컨테이너
- `.research-findings-container`: 조사 결과 컨테이너

## 📡 API 통신

### 엔드포인트 설정

`app.js`에서 API 엔드포인트를 설정합니다:

```javascript
const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocalDev ? 'http://localhost:8000' : window.location.origin;
const API_STREAM_URL = API_BASE_URL + '/api/chat/stream';
```

### 요청 형식

```javascript
const requestBody = {
    user_message: "분석하고 싶은 주제",
    session_id: "optional-session-id"
};
```

### SSE 이벤트 형식

```javascript
{
    type: "event_type",
    data: {...}
}
```

## 🎯 주요 기능 상세

### 세션 관리

- 자동 세션 ID 생성 및 관리
- 대화 히스토리 유지
- 세션별 컨텍스트 보존

### 에러 처리

- 네트워크 에러 처리
- 파싱 에러 처리
- 사용자 친화적 에러 메시지 표시

### 성능 최적화

- 메시지 렌더링 최적화
- Mermaid 다이어그램 지연 렌더링
- 스크롤 최적화

### 보고서 완료 처리

- writer 노드 완료 감지
- 검색창 및 전송 버튼 자동 비활성화
- 사용자에게 완료 상태 명확히 표시

## 🐛 문제 해결

### Mermaid 다이어그램이 렌더링되지 않음

- Mermaid.js 라이브러리가 로드되었는지 확인
- 브라우저 콘솔에서 에러 확인
- `data-processed` 속성 확인
- `renderMermaidDiagrams()` 함수가 올바르게 호출되는지 확인

### SSE 연결 실패

- 백엔드 서버가 실행 중인지 확인
- CORS 설정 확인
- 네트워크 탭에서 SSE 스트림 확인
- `sseClient.js`의 연결 로직 확인

### 마크다운이 제대로 파싱되지 않음

- Marked.js 라이브러리가 로드되었는지 확인
- 백틱 문제는 자동으로 수정됨
- 브라우저 콘솔에서 경고 확인
- `markdownUtils.js`의 파싱 로직 확인

### 검색창이 비활성화되지 않음

- writer 노드 완료 이벤트가 올바르게 수신되는지 확인
- `eventHandlers.js`의 `handleNodeCompleteEvent()` 확인
- `uiUpdater.js`의 `disableInput()` 메서드 확인

### 스트리밍이 중간에 멈춤

- 네트워크 연결 확인
- 백엔드 로그 확인
- 브라우저 개발자 도구에서 SSE 연결 상태 확인
- `sseClient.js`의 에러 처리 확인

## 📚 참고 자료

- [Marked.js 문서](https://marked.js.org/)
- [Mermaid.js 문서](https://mermaid.js.org/)
- [SSE 스펙](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Vanilla JavaScript 가이드](https://developer.mozilla.org/en-US/docs/Web/JavaScript)

## 🔄 리팩토링 히스토리

최근 대규모 리팩토링을 통해 코드 구조를 개선했습니다:

- **이전**: 899줄의 단일 `app.js` 파일
- **현재**: 모듈화된 구조로 분리
  - SSE 클라이언트 분리
  - 상태 관리 클래스화
  - 이벤트 핸들러 분리
  - UI 업데이트 로직 분리
  - 마크다운 유틸리티 모듈화

이를 통해 코드 가독성, 유지보수성, 테스트 용이성이 크게 향상되었습니다.

