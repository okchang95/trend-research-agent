# v1 대비 개선사항

본 문서는 Trend Agent v2.0의 주요 개선사항을 정리한 것입니다.  
각 개선사항은 SAR (Situation-Action-Result) 형식으로 작성되었습니다.

> **v1 참조**: v1 코드는 별도 브랜치에서 확인할 수 있습니다.

---

## 📊 개선 요약

### Frontend 개선

| 항목 | v1 | v2 |
|------|----|----|
| **프레임워크** | Vanilla JS | React 18 + TypeScript |
| **빌드 도구** | 없음 (CDN) | Vite |
| **상태 관리** | 전역 변수 | Context API + Custom Hooks |
| **라우팅** | 단일 페이지 | React Router (Thread별 URL) |
| **타입 안정성** | 없음 | TypeScript 완벽 지원 |

### Backend 개선

| 항목 | v1 | v2 |
|------|----|----|
| **데이터 저장** | 세션 기반 (메모리) | MongoDB 영구 저장 |
| **아키텍처** | 단일 모듈 | Repository + Service 패턴 |
| **Thread 관리** | 없음 | CRUD + 상태 관리 |
| **사용자 관리** | 없음 | User 시스템 |
| **백그라운드 처리** | 없음 | asyncio.Task + Queue 패턴 |

---

## 1. SSE 중간 상태 출력 기능 복구

### 📋 Situation (문제 인식)
- v1에서는 노드 상태, 리서치 상태, 조사 결과가 실시간으로 표시되었음
- React로 마이그레이션하면서 이 기능이 비활성화됨
- 사용자가 Agent의 진행 상황을 알 수 없어 UX가 저하됨

### 🔧 Action (해결 방법)
1. **새 React 컴포넌트 생성**
   - `NodeStatus.tsx`: Agent 노드 상태 표시
   - `ResearchStatus.tsx`: 리서치 상태 및 검색 결과 프리뷰
   - `ResearchFindings.tsx`: 상세 조사 결과 (토글 가능)

2. **Chat.tsx 상태 관리 추가**
   ```typescript
   const [nodeStatus, setNodeStatus] = useState<...>(null);
   const [researchStatus, setResearchStatus] = useState<...>(null);
   const [findings, setFindings] = useState<Finding[]>([]);
   ```

3. **SSE 이벤트 핸들러 구현**
   - `node_start`, `node_complete`: 노드 상태 업데이트
   - `research_status`: 리서치 진행 상황 업데이트
   - `research_findings`: 조사 결과 저장

### ✅ Result (결과)
- ✅ 사용자가 Agent의 진행 상황을 실시간으로 확인 가능
- ✅ 어떤 노드가 실행 중인지, 어떤 검색을 수행하는지 투명하게 표시
- ✅ v1 기능 완전 복구
- ✅ UX 대폭 개선

---

## 2. 조건부 자동 스크롤 구현

### 📋 Situation (문제 인식)
- 응답 생성 중 스크롤이 강제로 하단에 고정되어 사용자가 이전 내용을 읽을 수 없음
- 사용자가 스크롤을 올려도 계속 하단으로 이동하여 불편함 발생

### 🔧 Action (해결 방법)
```typescript
const handleScroll = useCallback(() => {
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
  // 하단 50px 이내면 자동 스크롤, 그렇지 않으면 비활성화
  setShouldAutoScroll(distanceFromBottom < 50);
}, []);

useEffect(() => {
  if (shouldAutoScroll) {
    messagesEndRef.current?.scrollIntoView({ behavior: 'auto' });
  }
}, [messages, streamingContent, shouldAutoScroll]);
```

### ✅ Result (결과)
- ✅ 사용자가 스크롤을 올리면 자동 스크롤 비활성화
- ✅ 하단으로 다시 스크롤하면 자동 스크롤 재활성화
- ✅ 이전 내용 확인하면서 새 내용도 놓치지 않음

---

## 3. UI 레이아웃 개선 (ChatGPT 스타일)

### 📋 Situation (문제 인식)
- Assistant 응답에 배경색과 테두리가 있어 시각적으로 복잡함
- 하단 입력창에 불필요한 테두리와 그림자가 있음

### 🔧 Action (해결 방법)
```css
/* Assistant 메시지 배경 제거 */
.assistant-message .message-content {
  background: transparent;
  border: none;
  padding: 0;
}

/* 입력창 테두리 제거 */
.input-section {
  border-top: none;
  box-shadow: none;
}
```

### ✅ Result (결과)
- ✅ 깔끔하고 현대적인 UI
- ✅ ChatGPT와 유사한 미니멀한 디자인
- ✅ 가독성 향상

---

## 4. Research Findings 영구 저장

### 📋 Situation (문제 인식)
- Research findings (출처 정보)가 스트리밍 중에만 표시되고 새로고침 시 사라짐
- DB에 저장되지 않아 나중에 확인 불가능

### 🔧 Action (해결 방법)
1. **Backend 모델 수정**
   ```python
   class ChatMessage(BaseModel):
       findings: Optional[List[dict]] = Field(default=None)
   ```

2. **Backend API 수정**
   - `service.py`: Agent 실행 후 findings 추출 및 저장
   - `schemas.py`: `ChatMessageResponse`에 findings 필드 추가

3. **Frontend 타입 정의**
   ```typescript
   export interface Message {
     findings?: Finding[];
   }
   ```

### ✅ Result (결과)
- ✅ Findings가 DB에 영구 저장됨
- ✅ 새로고침 후에도 출처 정보 확인 가능
- ✅ "조사 내용 보기" 토글 기능 복구

---

## 5. 응답 중지 버튼 추가

### 📋 Situation (문제 인식)
- 응답 생성 중 취소할 방법이 없음
- 잘못된 질문을 하거나 응답이 필요 없을 때 기다려야 함

### 🔧 Action (해결 방법)
1. **Frontend UI 변경**
   ```typescript
   {isStreaming ? (
     <button className="stop-btn" onClick={onStop}>
       <svg>■</svg>
     </button>
   ) : (
     <button className="search-btn">전송</button>
   )}
   ```

2. **중지 로직 구현**
   ```typescript
   const handleStopStream = useCallback(async () => {
     cancelStream();  // SSE 연결 끊기
     
     await fetch('/api/chat/cancel', {
       body: JSON.stringify({ thread_id, partial_message })
     });
   }, []);
   ```

### ✅ Result (결과)
- ✅ 사용자가 언제든지 응답 생성을 중단 가능
- ✅ "[응답이 중지되었습니다]" 메시지 저장
- ✅ 부분 생성된 내용도 함께 저장

---

## 6. Thread 상태 관리 시스템

### 📋 Situation (문제 인식)
- Thread가 응답 생성 중인지 알 수 없음
- 새로고침 후 다시 들어가면 어떤 상태인지 불명확

### 🔧 Action (해결 방법)
```python
class ThreadStatus(str, Enum):
    IDLE = "idle"           # 대기 중
    GENERATING = "generating"  # 응답 생성 중
    COMPLETED = "completed"    # 응답 완료
    ERROR = "error"           # 에러 발생
```

### ✅ Result (결과)
- ✅ Thread 상태가 명확히 관리됨
- ✅ 새로고침 후에도 상태 유지
- ✅ "응답 생성 중" 표시로 사용자에게 명확한 피드백

---

## 7. 비동기 + 큐 패턴으로 새로고침 시 응답 유실 방지

### 📋 Situation (문제 인식)
- **핵심 문제**: 응답 생성 중 새로고침하면 응답이 DB에 저장되지 않음
- SSE 연결 끊김 → Python generator 중단 → 백엔드 로직 멈춤

**시나리오:**
```
1. "2026 AI 트렌드 보고서 작성" 요청
2. Agent가 researcher 노드에서 작업 중
3. 사용자가 새로고침 (F5)
4. SSE 연결 끊김 → Generator 중단
5. finally 블록: if final_answer (None) → 저장 안 됨 ❌
```

### 🔧 Action (해결 방법)

#### 비동기 + 큐 패턴 도입
```python
event_queue = asyncio.Queue()

# 백그라운드 Task로 Agent 실행 (독립적)
background_task = asyncio.create_task(
    self._execute_conversation_flow(
        event_queue=event_queue,
        ...
    )
)

# SSE로 이벤트 전송
try:
    while True:
        event = await event_queue.get()
        if event is None:
            break
        yield event
except GeneratorExit:
    # ✅ 클라이언트 끊김, 하지만 background_task는 계속!
    logger.info("Client disconnected, agent continues")
    raise
```

#### 백그라운드 실행 및 저장
```python
async def _execute_conversation_flow(self, event_queue, ...):
    try:
        async for event in agent_runner.stream(...):
            await event_queue.put(event)
            
            if event.get("type") == "final":
                final_answer = state.get("answer")
        
        await event_queue.put(None)  # 종료 신호
        
        # ✅ DB 저장 (연결 끊겨도 실행!)
        if final_answer:
            await self._repo_chat_message.create(...)
            await self._repo_chat_thread.update(
                thread_id,
                {"status": ThreadStatus.COMPLETED}
            )
```

### ✅ Result (결과)

**동작 흐름:**
```
1. 요청 받음
   ↓
2. Background Task 시작 (독립적)
   ├─ Agent 실행
   ├─ event → Queue.put()
   └─ 계속 실행...
   
3. SSE Streaming
   ├─ Queue.get() → yield
   ├─ [새로고침!] → GeneratorExit
   └─ SSE 종료
   
4. Background Task (계속!)
   ├─ 남은 event 생성
   ├─ final event
   └─ DB 저장 ✅
```

**주요 개선사항:**
- ✅ Agent는 한 번만 실행 (비용/시간 낭비 없음)
- ✅ 새로고침해도 백그라운드에서 계속 실행
- ✅ 완료되면 자동으로 DB 저장
- ✅ Thread 상태 정확히 관리
- ✅ 데이터 유실 방지

---

## 8. 백그라운드 Task 취소 기능

### 📋 Situation (문제 인식)
- 중지 버튼을 눌러도 백그라운드 Agent는 계속 실행됨
- "[응답이 중지되었습니다]" 메시지 + 실제 보고서가 둘 다 저장됨
- 불필요한 API 비용 발생

### 🔧 Action (해결 방법)

**두 시나리오의 명확한 구분:**
1. **새로고침/페이지 이탈**: 백그라운드 작업 계속 → DB 저장 ✅
2. **중지 버튼 클릭**: 백그라운드 작업 즉시 중단 → DB 저장 X ✅

#### Cancel Event 패턴 도입
```python
class ChatService:
    def __init__(self, ...):
        # Task 저장소: thread_id -> (asyncio.Task, asyncio.Event)
        self._active_tasks: dict[str, tuple[asyncio.Task, asyncio.Event]] = {}
```

#### Task와 Cancel Event 함께 관리
```python
async def stream_conversation(self, ...):
    event_queue = asyncio.Queue()
    cancel_event = asyncio.Event()  # ✅ 취소 이벤트
    
    background_task = asyncio.create_task(
        self._execute_conversation_flow(..., cancel_event=cancel_event)
    )
    
    # ✅ Task와 cancel_event 함께 등록
    self._active_tasks[thread_id] = (background_task, cancel_event)
```

#### Agent에서 취소 체크
```python
async def _execute_conversation_flow(self, ..., cancel_event: asyncio.Event):
    try:
        async for event in self.agent_runner.stream(
            cancel_event=cancel_event,  # ✅ 전달
        ):
            # ✅ 주기적으로 취소 체크
            if cancel_event.is_set():
                logger.info("Cancellation requested")
                break
            
            await event_queue.put(event)
        
        # ✅ 취소되었으면 DB 저장하지 않음
        if cancel_event.is_set():
            logger.info("Skipping DB save (cancelled)")
            await update_status(ThreadStatus.IDLE)
            return
```

#### Graceful Shutdown
```python
async def cancel_stream(self, thread_id: str) -> bool:
    task_info = self._active_tasks.get(thread_id)
    
    if task_info:
        background_task, cancel_event = task_info
        
        # ✅ 1. cancel_event 설정 (graceful)
        cancel_event.set()
        
        # ✅ 2. 1초 대기 (정리 시간)
        try:
            await asyncio.wait_for(
                asyncio.shield(background_task),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            # ✅ 3. 안 끝나면 강제 취소
            background_task.cancel()
        
        self._active_tasks.pop(thread_id, None)
        return True
```

### ✅ Result (결과)

#### 시나리오 1: 새로고침/페이지 이탈
```
1. 응답 생성 중 새로고침 (F5)
2. SSE 연결 끊김 (GeneratorExit)
   └─ Backend: background_task 계속 실행 ✅
3. Background Task
   ├─ cancel_event.is_set() → False
   ├─ Agent 계속 실행
   └─ 완료 시 DB 저장 ✅
4. 다시 Thread 진입 → 완성된 응답 확인 가능 ✅
```

#### 시나리오 2: 중지 버튼 클릭
```
1. 중지 버튼 클릭
2. /api/chat/cancel-task 호출
   ├─ cancel_event.set() ✅
   └─ 1초 대기 (graceful shutdown)
3. Agent 감지 및 중단
   ├─ cancel_event.is_set() → True
   ├─ runner.py: astream_events 루프 break
   ├─ service.py: DB 저장 skip
   └─ Thread status → IDLE ✅
4. /api/chat/cancel 호출
   └─ "[응답이 중지되었습니다]" 메시지만 저장 ✅
```

**주요 개선사항:**
- ✅ Cancel Event 패턴으로 LangGraph 내부까지 취소 전파
- ✅ 두 시나리오 명확히 구분 (새로고침 vs 중지)
- ✅ Graceful Shutdown (1초 대기 → 강제 취소)
- ✅ 중지 버튼 클릭 시 Agent 즉시 중단
- ✅ 새로고침 시 백그라운드 작업 계속
- ✅ 불필요한 API 비용 절약
- ✅ 중복 메시지 방지

---

## 9. Thread별 독립 라우팅

### 📋 Situation (문제 인식)
- v1은 단일 페이지로 모든 Thread를 관리
- Thread 전환 시 전역 상태 초기화 필요
- 뒤로가기/앞으로가기 미지원

### 🔧 Action (해결 방법)
```typescript
// App.tsx
<Routes>
  <Route path="/" element={<Landing />} />
  <Route path="/chat" element={<Threads />} />
  <Route path="/chat/:threadId" element={<Chat />} />
</Routes>
```

### ✅ Result (결과)
- ✅ Thread별 독립적인 URL (`/chat/:threadId`)
- ✅ 브라우저 뒤로가기/앞으로가기 지원
- ✅ URL 공유 가능
- ✅ Thread별 독립적인 상태 관리

---

## 10. 사용 예시 UI 추가

### 📋 Situation (문제 인식)
- 처음 방문한 사용자가 어떻게 질문해야 할지 모름
- 빈 입력창만 보여서 진입 장벽이 높음

### 🔧 Action (해결 방법)
```typescript
// IntroSection.tsx
const examples = [
  {
    icon: '🤖',
    title: 'AI 에이전트 시장',
    query: '2026년 AI 에이전트 시장 전망과 주요 트렌드',
  },
  // ... 3개 더
];

<div className="example-card" onClick={() => onExampleClick(example.query)}>
  ...
</div>
```

### ✅ Result (결과)
- ✅ 클릭 가능한 예시 카드 4개
- ✅ 카드 클릭 시 자동 입력 및 전송
- ✅ 반응형 그리드 (데스크탑 2열, 모바일 1열)
- ✅ 사용자 진입 장벽 낮춤

---

## 종합 요약

### 개선 효과

**UX 개선:**
- ✅ 실시간 진행 상황 표시
- ✅ 자연스러운 스크롤 경험
- ✅ 깔끔한 ChatGPT 스타일 UI
- ✅ 언제든 응답 중지 가능
- ✅ Thread 상태 명확히 표시
- ✅ 사용 예시로 진입 장벽 낮춤

**안정성 개선:**
- ✅ 새로고침 시 데이터 유실 방지
- ✅ Research findings 영구 저장
- ✅ 에러 핸들링 강화
- ✅ Thread 상태 정확히 관리

**성능 개선:**
- ✅ Agent 중복 실행 방지
- ✅ 불필요한 API 비용 절약
- ✅ 메모리 누수 방지
- ✅ Task lifecycle 관리

**아키텍처 개선:**
- ✅ 비동기 + 큐 패턴 도입
- ✅ Task cancellation 구현
- ✅ 독립적인 백그라운드 실행
- ✅ 레이어드 아키텍처 (Repository + Service)
- ✅ TypeScript로 타입 안정성 확보

---

**버전:** 2.0.0  
**최종 업데이트:** 2026년 1월
