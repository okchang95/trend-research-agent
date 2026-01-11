# 아키텍처 문서

Trend Agent v2.0의 전체 시스템 아키텍처를 설명합니다.

## 📋 목차

- [전체 시스템 아키텍처](#전체-시스템-아키텍처)
- [Backend 아키텍처](#backend-아키텍처)
- [Frontend 아키텍처](#frontend-아키텍처)
- [데이터 흐름](#데이터-흐름)
- [SSE 스트리밍 아키텍처](#sse-스트리밍-아키텍처)
- [백그라운드 Task 관리](#백그라운드-task-관리)
- [데이터베이스 설계](#데이터베이스-설계)
- [보안 및 권한](#보안-및-권한)
- [배포 아키텍처](#배포-아키텍처)

---

## 🏗️ 전체 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client (Browser)                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              React Application (SPA)                     │   │
│  │  • React Router (Thread별 URL)                           │   │
│  │  • Context API (전역 상태)                                │   │
│  │  • useSSE Hook (SSE 스트리밍)                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Nginx (Reverse Proxy)                   │
│  • 정적 파일 서빙 (Frontend)                                     │
│  • API 요청 프록시 (/api → Backend)                             │
│  • SSL/TLS 종료                                                 │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Python)                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                      API Layer                           │   │
│  │  • Chat Router (/api/chat)                               │   │
│  │  • Users Router (/api/users)                             │   │
│  └───────────────────────┬──────────────────────────────────┘   │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐   │
│  │                   Service Layer                          │   │
│  │  • ChatService (비즈니스 로직)                             │   │
│  │  • ChatThreadService (Thread CRUD)                       │   │
│  │  • ChatMessageService (Message CRUD)                     │   │
│  │  • UserService (사용자 관리)                               │   │
│  └───────────────────────┬──────────────────────────────────┘   │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐   │
│  │                 Repository Layer                         │   │
│  │  • ChatThreadRepository                                  │   │
│  │  • ChatMessageRepository                                 │   │
│  │  • UserRepository                                        │   │
│  └───────────────────────┬──────────────────────────────────┘   │
│                          │                                      │
│  ┌───────────────────────▼──────────────────────────────────┐   │
│  │                  Agents Layer                            │   │
│  │  • LangGraph App (Workflow)                              │   │
│  │  • AgentRunner (실행 및 스트리밍)                          │   │
│  │  • Nodes (scoping, researcher, writer)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         MongoDB                                 │
│  • chat_threads (Thread 정보 및 상태)                            │
│  • chat_messages (메시지 및 findings)                            │
│  • users (사용자 정보)                                           │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     External Services                           │
│  • OpenAI (GPT-4o, GPT-4o-mini)                                 │
│  • Tavily (웹 검색)                                              │
│  • ArXiv (학술 논문 검색)                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 Backend 아키텍처

### 레이어드 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                        API Layer                            │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Router (FastAPI)                                    │    │
│  │ • HTTP 요청/응답 처리                                 │    │
│  │ • 요청 검증 (Pydantic)                                │    │
│  │ • 의존성 주입 (Depends)                               │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Service Layer                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Business Logic                                      │    │
│  │ • 비즈니스 규칙 구현                                   │    │
│  │ • Transaction 관리                                   │    │
│  │ • Agent 실행 및 스트리밍                              │    │
│  │ • 백그라운드 Task 관리                                │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Repository Layer                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Data Access                                         │    │
│  │ • CRUD 연산                                          │    │
│  │ • 쿼리 구성                                          │    │
│  │ • 데이터 변환 (MongoDB ↔ Pydantic)                   │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Database                               │
│                     MongoDB                                 │
└─────────────────────────────────────────────────────────────┘
```

### LangGraph Agent 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph App                            │
│                                                             │
│  ┌───────────┐                                              │
│  │   START   │                                              │
│  └─────┬─────┘                                              │
│        │                                                    │
│  ┌─────▼──────────────┐                                     │
│  │  clarify_requirement│                                     │
│  │     (Scoping Node) │                                     │
│  └─────┬──────────────┘                                     │
│        │                                                    │
│        ├─── is_clarified=False ──→ [END]                    │
│        │    (일반 대화)                                      │
│        │                                                    │
│        └─── is_clarified=True                               │
│             (트렌드 분석 요청)                                │
│             │                                               │
│  ┌──────────▼────────────────────────────────────────────┐  │
│  │           Researcher SubGraph                        │  │
│  │  ┌──────────────┐        ┌──────────────┐           │  │
│  │  │  Agent Node  │◄──────►│  Tools Node  │           │  │
│  │  │ (LLM 추론)    │        │ (도구 실행)   │           │  │
│  │  └──────────────┘        └──────────────┘           │  │
│  │        │                        │                    │  │
│  │        │   should_continue?     │                    │  │
│  │        └────────┬───────────────┘                    │  │
│  │                 │ (최대 3회 반복)                     │  │
│  │                 │                                    │  │
│  │  Tools:                                              │  │
│  │  • tavily_search (웹 검색)                            │  │
│  │  • arxiv_search (논문 검색)                           │  │
│  └──────────────────┬──────────────────────────────────┘  │
│                     │                                     │
│  ┌──────────────────▼──────────────────────────────────┐  │
│  │              Writer Node                            │  │
│  │         (보고서 작성)                                 │  │
│  └──────────────────┬──────────────────────────────────┘  │
│                     │                                     │
│  ┌──────────────────▼──────────────────────────────────┐  │
│  │                  END                                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Agent State

```python
class AgentState(TypedDict):
    # 입력
    user_message: str
    conversations: List[ChatMessage]
    conversations_summary: str
    
    # Scoping 출력
    is_clarified: bool
    subject: str
    scope: str
    brief_requirement: str
    answer: str  # scoping 단계 응답
    
    # Research 출력
    findings: List[Finding]
    
    # Writer 출력
    # answer 필드 재사용 (최종 보고서)
    
    # 메타데이터
    current_node: str
    ended_node: str
```

---

## 🎨 Frontend 아키텍처

### 컴포넌트 계층 구조

```
App (Router)
├── Landing Page (/)
│   └── 서비스 소개
│
├── Threads Page (/chat)
│   ├── Sidebar
│   │   ├── Logo
│   │   ├── New Thread Button
│   │   └── Thread List
│   ├── IntroSection
│   │   └── Example Cards
│   └── InputSection
│
└── Chat Page (/chat/:threadId)
    ├── Sidebar (동일)
    ├── MessageList
    │   ├── Messages
    │   │   ├── UserMessage
    │   │   └── AssistantMessage
    │   │       └── Markdown (Marked + Mermaid)
    │   ├── StreamingStatus
    │   │   ├── NodeStatus
    │   │   ├── ResearchStatus
    │   │   └── StreamingContent
    │   └── ResearchFindings (토글)
    └── InputSection
```

### 상태 관리 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    Global State (Context)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ AuthContext                                          │   │
│  │ • userId                                             │   │
│  │ • setUserId                                          │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ChatContext                                          │   │
│  │ • threads (Thread[])                                 │   │
│  │ • currentThreadId                                    │   │
│  │ • messages (Message[])                               │   │
│  │ • addMessage()                                       │   │
│  │ • clearChat()                                        │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Page Level State                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Chat.tsx (Thread별 독립 상태)                         │   │
│  │ • messages (로컬 상태)                                │   │
│  │ • streamingContent                                   │   │
│  │ • nodeStatus                                         │   │
│  │ • researchStatus                                     │   │
│  │ • findings                                           │   │
│  │ • shouldAutoScroll                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Custom Hooks                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ useSSE                                               │   │
│  │ • streamingThreads (Set<threadId>)                   │   │
│  │ • streamStatesRef (Map<threadId, AbortController>)   │   │
│  │ • stream(threadId, body, onEvent)                    │   │
│  │ • cancelStream(threadId)                             │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 데이터 흐름

### 1. 새 대화 시작 (메인 페이지)

```
[사용자 입력]
      │
      ▼
1. Threads.tsx: createThread(userId)
      │
      ▼
2. Backend: POST /api/chat/threads
      │
      ├─ ChatThreadService.create_thread()
      ├─ ChatThreadRepository.create()
      └─ MongoDB: chat_threads 컬렉션에 저장
      │
      ▼
3. Frontend: navigate(`/chat/${newThreadId}`, { state: { initialMessage } })
```

### 2. 메시지 전송 및 스트리밍

```
[메시지 전송]
      │
      ▼
1. Chat.tsx: handleSendMessage()
      │
      ├─ 낙관적 업데이트: 사용자 메시지 즉시 표시
      │
      ▼
2. useSSE.stream(threadId, requestBody, handleSSEEvent)
      │
      ▼
3. Backend: POST /api/chat/stream
      │
      ├─ ChatService.stream_conversation()
      │   │
      │   ├─ asyncio.Queue 생성
      │   ├─ asyncio.Event (cancel_event) 생성
      │   │
      │   ├─ Background Task 시작
      │   │   ├─ _execute_conversation_flow()
      │   │   │   ├─ Agent 실행
      │   │   │   ├─ Event → Queue.put()
      │   │   │   └─ 완료 시 DB 저장
      │   │   │
      │   │   └─ _active_tasks에 등록
      │   │
      │   └─ SSE Generator
      │       ├─ Queue.get() → yield
      │       └─ 클라이언트 끊김 처리
      │
      ▼
4. Frontend: handleSSEEvent()
      │
      ├─ 'thread': Thread 정보 업데이트
      ├─ 'node_start': 노드 상태 표시
      ├─ 'research_status': 리서치 진행 상황
      ├─ 'text_chunk': 스트리밍 텍스트 추가
      ├─ 'research_findings': Findings 저장
      └─ 'final': 최종 결과 → DB에서 메시지 다시 로드
```

### 3. 새로고침 시나리오

```
[사용자가 새로고침]
      │
      ▼
1. SSE 연결 끊김 (GeneratorExit)
      │
      ├─ Frontend: SSE 스트림 종료
      │
      └─ Backend: Generator 종료
           │
           ├─ Background Task는 계속 실행! ✅
           │   │
           │   ├─ Agent 실행 계속
           │   ├─ Queue에 이벤트 계속 추가 (소비자 없음)
           │   └─ 완료 시 DB 저장
           │
           └─ Thread status → COMPLETED
      │
      ▼
2. 페이지 재로드
      │
      ▼
3. Chat.tsx: useEffect()
      │
      ├─ loadThreadMessages(threadId)
      │   │
      │   └─ GET /api/chat/threads/{id}/messages
      │
      └─ Thread status 확인
           │
           ├─ GENERATING → "응답 생성 중" 표시
           └─ COMPLETED → 완성된 메시지 표시 ✅
```

### 4. 응답 중지 시나리오

```
[중지 버튼 클릭]
      │
      ▼
1. handleStopStream()
      │
      ├─ cancelStream(threadId)  // SSE 끊기
      │
      ├─ POST /api/chat/cancel-task
      │   │
      │   ├─ ChatService.cancel_stream(threadId)
      │   │   │
      │   │   ├─ cancel_event.set() ✅
      │   │   ├─ 1초 대기 (graceful shutdown)
      │   │   └─ 안 끝나면 task.cancel()
      │   │
      │   └─ Agent에서 취소 감지
      │       │
      │       ├─ if cancel_event.is_set(): break
      │       └─ DB 저장 skip
      │
      └─ POST /api/chat/cancel
           │
           └─ "[응답이 중지되었습니다]" 메시지 저장
```

---

## 📡 SSE 스트리밍 아키텍처

### SSE 이벤트 타입

```typescript
type SSEEvent = 
  | { type: 'thread'; thread_id: string; title?: string }
  | { type: 'node_start'; node: string }
  | { type: 'node_complete'; node: string }
  | { type: 'research_status'; status: string; query?: string }
  | { type: 'research_findings'; findings: Finding[] }
  | { type: 'text_chunk'; content: string }
  | { type: 'final'; state: FinalState }
  | { type: 'error'; message: string };
```

### Backend: Event Generation

```python
# agents/streaming/event_handlers.py
class StreamEventHandler:
    def handle(self, event: dict) -> Iterator[dict]:
        event_type = event.get("event")
        
        if event_type == "on_chain_start":
            yield self.handle_chain_start(event)
        
        elif event_type == "on_chat_model_stream":
            yield self.handle_model_stream(event)
        
        elif event_type == "on_tool_start":
            yield self.handle_tool_start(event)
        
        # ... 기타 이벤트 처리
```

### Frontend: Event Handling

```typescript
// hooks/useSSE.ts
const stream = async (threadId: string, body: any, onEvent: (e: SSEEvent) => void) => {
  const abortController = new AbortController();
  
  const response = await fetch(API_STREAM_URL, {
    method: 'POST',
    body: JSON.stringify(body),
    signal: abortController.signal,
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    // SSE 파싱
    const text = decoder.decode(value);
    const lines = text.split('\n\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const event = JSON.parse(line.slice(6));
        onEvent(event);  // 이벤트 핸들러 호출
      }
    }
  }
};
```

---

## ⚙️ 백그라운드 Task 관리

### Task Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                   Task 생명주기                              │
│                                                             │
│  1. 생성 (CREATE)                                            │
│     background_task = asyncio.create_task(...)              │
│     self._active_tasks[thread_id] = (task, cancel_event)    │
│                                                             │
│  2. 실행 (RUNNING)                                           │
│     Agent 실행 → Event Queue → SSE 전송                      │
│                                                             │
│  3. 완료 (COMPLETED)                                         │
│     DB 저장 → Queue.put(None) → Task 종료                    │
│     self._active_tasks.pop(thread_id)                       │
│                                                             │
│  4. 취소 (CANCELLED) - 선택적                                │
│     cancel_event.set()                                      │
│     1초 대기 → task.cancel()                                │
│     self._active_tasks.pop(thread_id)                       │
└─────────────────────────────────────────────────────────────┘
```

### Task 저장소

```python
class ChatService:
    def __init__(self, ...):
        # thread_id → (Task, Event)
        self._active_tasks: Dict[str, Tuple[asyncio.Task, asyncio.Event]] = {}
    
    async def stream_conversation(self, thread_id: str, ...):
        cancel_event = asyncio.Event()
        task = asyncio.create_task(
            self._execute_conversation_flow(..., cancel_event)
        )
        self._active_tasks[thread_id] = (task, cancel_event)
    
    async def cancel_stream(self, thread_id: str) -> bool:
        if thread_id in self._active_tasks:
            task, cancel_event = self._active_tasks[thread_id]
            cancel_event.set()
            # Graceful shutdown
            try:
                await asyncio.wait_for(task, timeout=1.0)
            except asyncio.TimeoutError:
                task.cancel()
            self._active_tasks.pop(thread_id)
            return True
        return False
```

---

## 💾 데이터베이스 설계

### MongoDB 컬렉션

#### 1. chat_threads

```javascript
{
  _id: ObjectId("..."),
  user_id: ObjectId("..."),
  title: "New Thread",
  status: "idle" | "generating" | "completed" | "error",
  conversation_summary: "",
  last_summarized_at: ISODate("..."),
  created_at: ISODate("..."),
  updated_at: ISODate("...")
}
```

**인덱스:**
- `user_id` (조회 성능)
- `created_at` (정렬)

#### 2. chat_messages

```javascript
{
  _id: ObjectId("..."),
  thread_id: ObjectId("..."),
  role: "user" | "assistant",
  message: "...",
  ended_node: "scoping" | "researcher" | "writer" | null,
  report_summary: "...",  // 보고서 요약 (writer 노드)
  findings: [              // 출처 정보 (writer 노드)
    {
      query: "...",
      source: "tavily" | "arxiv",
      results: [
        {
          title: "...",
          url: "...",
          content: "...",
          score: 0.95
        }
      ]
    }
  ],
  timestamp: ISODate("...")
}
```

**인덱스:**
- `thread_id` (Thread별 메시지 조회)
- `timestamp` (시간순 정렬)

#### 3. users

```javascript
{
  _id: ObjectId("..."),
  username: "user123",
  created_at: ISODate("..."),
  last_login: ISODate("...")
}
```

**인덱스:**
- `username` (unique)

---

## 🔒 보안 및 권한

### Thread 접근 제어

```python
# service.py
async def get_thread_by_id(self, thread_id: str, user_id: str = None):
    thread = await self._repo.get_by_oid(thread_id)
    
    if not thread:
        return None
    
    # user_id가 제공된 경우 권한 검증
    if user_id and str(thread["user_id"]) != user_id:
        raise ValueError("You don't have permission to access this thread")
    
    return thread
```

### API 레벨 검증

```python
# router.py
@router.post("/chat/stream")
async def stream_chat(
    payload: ChatRequest,
    service: ChatService = Depends(get_chat_service),
):
    # 1. Thread 존재 확인
    thread = await service.get_thread_by_id(
        payload.thread_id,
        user_id=payload.user_id  # 권한 검증
    )
    
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # 2. 스트리밍 시작
    return StreamingResponse(
        service.stream_conversation(...),
        media_type="text/event-stream"
    )
```

---

## 🚀 배포 아키텍처

### Docker Compose 구성

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Network                         │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   nginx      │  │   backend    │  │   mongodb    │      │
│  │   (80/443)   │  │   (8000)     │  │   (27017)    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                 │                 │              │
│         │  /api/*         │                 │              │
│         │────────────────►│                 │              │
│         │                 │  MongoDB Driver │              │
│         │                 │────────────────►│              │
│         │                 │                 │              │
│  ┌──────▼───────┐         │                 │              │
│  │  Frontend    │         │                 │              │
│  │  (dist/)     │         │                 │              │
│  └──────────────┘         │                 │              │
│                           │                 │              │
│                      ┌────▼─────┐           │              │
│                      │ OpenAI   │           │              │
│                      │ Tavily   │           │              │
│                      │ ArXiv    │           │              │
│                      └──────────┘           │              │
└─────────────────────────────────────────────────────────────┘
```

### 환경별 설정

**개발 환경** (`docker-compose.dev.yml`):
- Hot reload 활성화
- 디버그 로그
- 로컬 볼륨 마운트

**프로덕션 환경** (`docker-compose.prod.yml`):
- 최적화된 빌드
- 환경 변수로 민감 정보 관리
- 헬스 체크
- 재시작 정책

---

## 📊 성능 고려사항

### Backend 최적화

1. **비동기 I/O**
   - FastAPI + asyncio
   - Motor (async MongoDB driver)
   - 동시성 처리

2. **백그라운드 Task**
   - 긴 작업을 백그라운드로 분리
   - SSE 연결 독립성 확보

3. **데이터베이스 인덱스**
   - 자주 조회되는 필드 인덱싱
   - 복합 인덱스 활용

### Frontend 최적화

1. **코드 스플리팅**
   - React Router 기반 페이지별 분할
   - Dynamic import

2. **메모이제이션**
   - `useCallback`, `useMemo` 활용
   - 불필요한 리렌더링 방지

3. **SSE 연결 관리**
   - Thread별 독립적인 AbortController
   - 메모리 누수 방지

---

**버전:** 2.0.0  
**최종 업데이트:** 2026년 1월
