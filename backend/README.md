# Backend - Trend Agent API

FastAPI 기반의 AI 트렌드 분석 에이전트 백엔드 서비스입니다.

## 📋 목차

- [아키텍처](#아키텍처)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [핵심 모듈](#핵심-모듈)
- [API 엔드포인트](#api-엔드포인트)
- [v1 대비 개선사항](#v1-대비-개선사항)
- [설치 및 실행](#설치-및-실행)
- [개발 가이드](#개발-가이드)

---

## 🏗️ 아키텍처

### 레이어드 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                      API Layer                          │
│  ┌───────────────────┐  ┌───────────────────┐          │
│  │   Chat Router     │  │   Users Router    │          │
│  │  /api/chat/*      │  │  /api/users/*     │          │
│  └─────────┬─────────┘  └─────────┬─────────┘          │
└────────────┼────────────────────────┼───────────────────┘
             │                        │
┌────────────┼────────────────────────┼───────────────────┐
│            │     Service Layer      │                   │
│  ┌─────────▼─────────┐  ┌──────────▼────────┐          │
│  │  ChatService      │  │  UserService      │          │
│  │  (비즈니스 로직)   │  │  (사용자 관리)     │          │
│  │                   │  │                    │          │
│  │  ChatThreadService│  │                    │          │
│  │  ChatMessageService│ │                    │          │
│  └─────────┬─────────┘  └──────────┬────────┘          │
└────────────┼────────────────────────┼───────────────────┘
             │                        │
┌────────────┼────────────────────────┼───────────────────┐
│            │   Repository Layer     │                   │
│  ┌─────────▼─────────┐  ┌──────────▼────────┐          │
│  │ ChatThreadRepo    │  │  UserRepository   │          │
│  │ ChatMessageRepo   │  │                    │          │
│  └─────────┬─────────┘  └──────────┬────────┘          │
└────────────┼────────────────────────┼───────────────────┘
             │                        │
             ▼                        ▼
┌─────────────────────────────────────────────────────────┐
│                      MongoDB                            │
│    chat_threads  │  chat_messages  │  users            │
└─────────────────────────────────────────────────────────┘
```

### Agent 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│                    AgentRunner                          │
│  (LangGraph 래퍼, 스트리밍 관리)                         │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   LangGraph App                         │
│                                                         │
│  ┌─────────────┐                                        │
│  │   START     │                                        │
│  └──────┬──────┘                                        │
│         │                                               │
│  ┌──────▼──────┐    is_clarified=False    ┌──────────┐ │
│  │   Scoping   │◄────────────────────────►│   END    │ │
│  │   Node      │    (일반 대화 응답)        └──────────┘ │
│  └──────┬──────┘                                        │
│         │ is_clarified=True                             │
│  ┌──────▼──────────────────────────────────────────┐   │
│  │              Researcher SubGraph                 │   │
│  │  ┌──────────┐       ┌──────────────┐            │   │
│  │  │ Agent    │◄─────►│ Tools Node   │            │   │
│  │  │ Node     │       │ (웹/논문검색) │            │   │
│  │  └──────────┘       └──────────────┘            │   │
│  │        ↑                   │                     │   │
│  │        └───────────────────┘                     │   │
│  │              (최대 3회 반복)                      │   │
│  └──────────────────────┬──────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼──────────────────────────┐   │
│  │                 Writer Node                      │   │
│  │            (마크다운 보고서 생성)                  │   │
│  └──────────────────────┬──────────────────────────┘   │
│                         │                               │
│  ┌──────────────────────▼──────────────────────────┐   │
│  │                     END                          │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ 기술 스택

| 카테고리 | 기술 | 버전 | 용도 |
|---------|------|------|------|
| **Framework** | FastAPI | 0.128+ | 비동기 웹 프레임워크 |
| **AI/LLM** | LangGraph | 1.0+ | 에이전트 워크플로우 |
| | LangChain | 1.2+ | LLM 통합 |
| | OpenAI | 2.14+ | GPT 모델 |
| **Database** | MongoDB | 4.16+ | 데이터 저장 |
| | Motor | - | 비동기 MongoDB 드라이버 |
| **Search** | Tavily | - | 웹 검색 API |
| | ArXiv | 2.3+ | 학술 논문 검색 |
| **Validation** | Pydantic | 2.12+ | 데이터 검증 |

---

## 📁 프로젝트 구조

```
backend/
├── app/
│   ├── agents/                  # LangGraph 에이전트
│   │   ├── nodes/               # 노드 구현
│   │   │   ├── scoping.py       # 요구사항 명확화 노드
│   │   │   ├── researcher.py    # 정보 수집 노드 (ReAct)
│   │   │   ├── writer.py        # 보고서 작성 노드
│   │   │   └── research_tools.py # 검색 도구 정의
│   │   ├── streaming/           # SSE 스트리밍
│   │   │   ├── event_handlers.py # 이벤트 핸들러
│   │   │   └── streaming_utils.py # 유틸리티
│   │   ├── graph.py             # LangGraph 그래프 정의
│   │   ├── runner.py            # 에이전트 실행기
│   │   ├── state.py             # 에이전트 상태 정의
│   │   ├── prompts.py           # 프롬프트 템플릿
│   │   └── utils.py             # 유틸리티
│   │
│   ├── api/                     # API 레이어
│   │   ├── chat/                # 채팅 API
│   │   │   ├── router.py        # 라우터 정의
│   │   │   ├── service.py       # 비즈니스 로직
│   │   │   ├── repository.py    # 데이터 액세스
│   │   │   ├── models.py        # Pydantic 모델
│   │   │   ├── schemas.py       # API 스키마
│   │   │   ├── deps.py          # 의존성 주입
│   │   │   └── sse.py           # SSE 유틸리티
│   │   └── users/               # 사용자 API
│   │       ├── router.py
│   │       ├── service.py
│   │       ├── repository.py
│   │       ├── models.py
│   │       └── schemas.py
│   │
│   ├── core/                    # 핵심 설정
│   │   ├── config.py            # 환경 변수 설정
│   │   ├── lifespan.py          # 앱 생명주기 관리
│   │   ├── llm.py               # LLM 초기화
│   │   ├── logging.py           # 로깅 설정
│   │   └── response.py          # 응답 유틸리티
│   │
│   ├── db/                      # 데이터베이스
│   │   ├── collections.py       # 컬렉션 정의
│   │   ├── deps.py              # DB 의존성
│   │   ├── types.py             # 커스텀 타입
│   │   └── utils.py             # DB 유틸리티
│   │
│   └── main.py                  # FastAPI 앱 진입점
│
├── logs/                        # 로그 파일
├── requirements.txt             # Python 의존성
└── Dockerfile                   # Docker 이미지
```

---

## 🔧 핵심 모듈

### 1. ChatService (비동기 + 큐 패턴)

**핵심 기능:** SSE 스트리밍 중 새로고침해도 Agent가 계속 실행되어 데이터 유실 방지

```python
async def stream_conversation(self, ...):
    event_queue = asyncio.Queue()
    cancel_event = asyncio.Event()
    
    # 백그라운드 Task로 Agent 실행 (독립적)
    background_task = asyncio.create_task(
        self._execute_conversation_flow(
            event_queue=event_queue,
            cancel_event=cancel_event,
            ...
        )
    )
    
    # Task 등록 (취소 관리용)
    self._active_tasks[thread_id] = (background_task, cancel_event)
    
    # SSE로 이벤트 전송
    try:
        while True:
            event = await event_queue.get()
            if event is None:
                break
            yield event
    except GeneratorExit:
        # 클라이언트 끊김, 하지만 background_task는 계속!
        logger.info("Client disconnected, agent continues")
        raise
```

### 2. AgentRunner (LangGraph 래퍼)

**핵심 기능:** LangGraph 이벤트를 SSE 형식으로 변환

```python
async def stream(self, cancel_event: asyncio.Event = None):
    async for event in self.graph_app.astream_events(...):
        # 취소 체크
        if cancel_event and cancel_event.is_set():
            break
        
        # 이벤트 핸들러로 SSE 이벤트 생성
        for sse_event in handler.handle(event):
            yield sse_event
```

### 3. Repository 패턴

**핵심 기능:** 데이터 액세스 로직 분리

```python
class ChatThreadRepository:
    def __init__(self, db: Database):
        self._col = db[MongoCollections.CHAT_THREADS]
    
    async def create(self, data: dict): ...
    async def get_by_oid(self, oid: str): ...
    async def get_all_by_user_id(self, user_id: str): ...
    async def update(self, oid: str, update_set: dict): ...
    async def delete(self, oid: str): ...
```

---

## 📡 API 엔드포인트

### Chat API (`/api/chat`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/stream` | SSE 스트리밍 채팅 |
| `GET` | `/threads` | Thread 목록 조회 |
| `POST` | `/threads` | Thread 생성 |
| `DELETE` | `/threads/{id}` | Thread 삭제 |
| `GET` | `/threads/{id}/messages` | 메시지 조회 |
| `POST` | `/cancel` | 응답 중지 메시지 저장 |
| `POST` | `/cancel-task` | 백그라운드 작업 취소 |

### Users API (`/api/users`)

| Method | Endpoint | 설명 |
|--------|----------|------|
| `POST` | `/users` | 사용자 생성/조회 |

### SSE 이벤트 타입

| 타입 | 설명 |
|------|------|
| `thread` | Thread 정보 (ID, 제목) |
| `node_start` | 노드 시작 알림 |
| `node_complete` | 노드 완료 알림 |
| `research_status` | 리서치 진행 상황 |
| `research_findings` | 조사 결과 |
| `text_chunk` | 스트리밍 텍스트 청크 |
| `final` | 최종 결과 |
| `error` | 에러 발생 |

---

## 🚀 v1 대비 개선사항

### 1. 데이터 영구 저장

| 항목 | v1 | v2 |
|------|----|----|
| 저장 방식 | 세션 (메모리) | MongoDB |
| 대화 기록 | 새로고침 시 유실 | 영구 보존 |
| Findings | 저장 안 됨 | DB에 저장 |

### 2. 아키텍처 개선

| 항목 | v1 | v2 |
|------|----|----|
| 구조 | 단일 모듈 | 레이어드 아키텍처 |
| 데이터 액세스 | 직접 접근 | Repository 패턴 |
| 비즈니스 로직 | 라우터에 혼재 | Service 레이어 분리 |

### 3. 비동기 + 큐 패턴

**문제:** 새로고침 시 SSE 연결 끊김 → Agent 중단 → 데이터 유실

**해결:**
```
요청 → Background Task (독립) → Agent 실행
         ↓
      Event Queue → SSE 전송
         ↓
      [새로고침] → SSE 끊김, Task 계속!
         ↓
      Agent 완료 → DB 저장 ✅
```

### 4. Task 취소 기능

**문제:** 중지 버튼 눌러도 Agent가 끝까지 실행 (API 비용 낭비)

**해결:**
- `cancel_event` 패턴으로 LangGraph 내부까지 취소 전파
- Graceful Shutdown (1초 대기 → 강제 취소)

### 5. Thread 상태 관리

```python
class ThreadStatus(str, Enum):
    IDLE = "idle"           # 대기 중
    GENERATING = "generating"  # 응답 생성 중
    COMPLETED = "completed"    # 응답 완료
    ERROR = "error"           # 에러 발생
```

---

## 🔧 설치 및 실행

### 환경 변수

```bash
# .env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=trend_agent_db

# 선택사항 (LangSmith)
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your_langsmith_api_key
```

### 로컬 실행

```bash
# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행
uvicorn app.main:app --reload --port 8000
```

### Docker 실행

```bash
docker build -t trend-agent-backend .
docker run -p 8000:8000 --env-file .env trend-agent-backend
```

---

## 📝 개발 가이드

### 새로운 노드 추가

1. `app/agents/nodes/`에 노드 파일 생성
2. `AgentState`를 입력/출력으로 하는 함수 작성
3. `app/agents/graph.py`에 노드 추가 및 엣지 연결

```python
# 예: app/agents/nodes/my_node.py
from app.agents.state import AgentState

async def my_node(state: AgentState) -> AgentState:
    # 로직 구현
    return {"my_field": result}
```

### 새로운 도구 추가

1. `app/agents/nodes/research_tools.py`에 도구 정의
2. `get_tools_map()`에 도구 추가
3. `execute_tool()`에 실행 로직 추가

```python
# 예: 새로운 검색 도구
my_tool = StructuredTool.from_function(
    func=my_search_function,
    name="my_search",
    description="검색 도구 설명",
)
```

---

## 📊 성능 및 제한사항

| 항목 | 값 |
|------|-----|
| 최대 반복 횟수 | 3회 (researcher) |
| 웹 검색 결과 수 | 최대 5개 |
| 논문 검색 결과 수 | 최대 3개 |
| 예상 응답 시간 | 30초 ~ 2분 |

---

**버전:** 2.0.0  
**최종 업데이트:** 2026년 1월
