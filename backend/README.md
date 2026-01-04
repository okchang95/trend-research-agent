# Backend - AI 트렌드 분석 어시스턴트

FastAPI 기반 백엔드 서버로, LangGraph를 사용한 에이전트 워크플로우와 SSE 스트리밍을 제공합니다.

## 🛠 기술 스택

- **FastAPI**: 고성능 비동기 웹 프레임워크
- **LangGraph**: 에이전트 워크플로우 관리 및 상태 관리
- **LangChain**: LLM 통합 및 도구 사용
- **OpenAI**: GPT 모델
- **Tavily**: 웹 검색 API
- **ArXiv**: 학술 논문 검색
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증 및 스키마 정의
- **Python 3.11+**: 최신 Python 기능 활용

## 📁 프로젝트 구조

```
backend/
├── app/
│   ├── agents/              # 에이전트 관련 모듈
│   │   ├── graph.py         # LangGraph 그래프 정의
│   │   ├── runner.py        # 에이전트 실행기
│   │   ├── state.py         # 에이전트 상태 정의
│   │   ├── prompts.py       # 프롬프트 정의
│   │   ├── utils.py         # 유틸리티 함수
│   │   ├── steaming/        # 스트리밍 관련 모듈
│   │   │   ├── event_handlers.py # 스트리밍 이벤트 핸들러
│   │   │   └── streaming_utils.py # 스트리밍 유틸리티
│   │   └── nodes/           # 에이전트 노드
│   │       ├── scoping.py        # 요구사항 명확화 노드
│   │       ├── researcher.py     # 정보 수집 노드 (ReAct 패턴)
│   │       ├── writer.py         # 보고서 작성 노드
│   │       └── research_tools.py  # 도구 정의 및 실행 로직
│   ├── api/                 # API 레이어
│   │   ├── router.py        # FastAPI 라우터
│   │   ├── service.py       # 비즈니스 로직
│   │   ├── schemas.py       # Pydantic 스키마
│   │   ├── session.py       # 세션 관리
│   │   └── sse.py           # SSE 유틸리티
│   ├── core/                # 핵심 설정
│   │   ├── config.py        # 환경 변수 설정
│   │   ├── llm.py          # LLM 초기화
│   │   └── logging.py      # 로깅 설정
│   └── main.py              # FastAPI 애플리케이션 진입점
├── requirements.txt         # Python 의존성
└── Dockerfile              # Docker 이미지 정의
```

## 🚀 설치 및 실행

### 환경 변수 설정

`backend/.env` 파일을 생성하고 다음 변수를 설정하세요:

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key

# LangSmith (선택사항)
LANGCHAIN_TRACING_V2=false
LANGSMITH_API_KEY=
LANGSMITH_ENDPOINT=
LANGSMITH_PROJECT=
```

### 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

### 개발 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

서버는 `http://localhost:8000`에서 실행됩니다.

### Docker로 실행

```bash
docker build -t research-agent-backend .
docker run -p 8000:8000 --env-file .env research-agent-backend
```

또는 docker-compose 사용:

```bash
docker-compose up backend
```

## 📡 API 엔드포인트

### POST `/api/chat/stream`

SSE 스트리밍 채팅 요청

**Request:**
```json
{
  "session_id": "optional-session-id",
  "user_message": "최근 AI 트렌드 분석해줘"
}
```

**Response:** SSE 스트림

**이벤트 타입:**
- `session`: 세션 ID 전송
- `node_start`: 노드 시작
- `node_complete`: 노드 완료
- `research_status`: 조사 상태 업데이트
- `research_findings`: 조사 결과
- `text_chunk`: 텍스트 청크 (스트리밍)
- `scoping_complete`: 요구사항 명확화 완료
- `final`: 최종 결과
- `error`: 에러 발생

### GET `/api/sessions`

모든 세션 목록 조회

**Response:**
```json
[
  {
    "session_id": "session-id",
    "conversations": [...],
    "conversations_summary": "..."
  }
]
```

### GET `/health`

헬스 체크

**Response:**
```json
{
  "status": "ok"
}
```

## 🏗 모듈 상세 설명

### Agents 모듈

#### `graph.py`
- LangGraph 그래프 정의
- 노드 추가 및 엣지 연결
- `graph_builder()` 함수로 그래프 생성

#### `runner.py`
- `AgentRunner` 클래스: 에이전트 실행 및 스트리밍 관리
- `stream()` 메서드: SSE 스트리밍 실행
- LangGraph의 `astream_events` 활용

#### `state.py`
- `AgentState` TypedDict 정의
- 에이전트 전역 상태 관리

#### `prompts.py`
- 각 노드별 시스템/사용자 프롬프트 정의
- `SCOPING_SYSTEM_PROMPT`, `RESEARCH_SYSTEM_PROMPT`, `WRITING_SYSTEM_PROMPT` 등

#### `nodes/scoping.py`
- 요구사항 명확화 노드
- Pydantic 모델로 구조화된 출력
- `is_clarified` 플래그로 다음 노드 결정

#### `nodes/researcher.py`
- ReAct 패턴 구현
- 서브그래프로 `agent_node`와 `tools_node` 분리
- 최대 3회 반복을 통한 정보 수집
- `_build_research_graph()` 함수로 서브그래프 생성

#### `nodes/writer.py`
- 보고서 작성 노드
- findings를 바탕으로 마크다운 보고서 생성
- 테이블, 다이어그램, 출처 포함

#### `nodes/research_tools.py`
- 도구 정의 및 실행 로직
- `tavily_search`: Tavily 웹 검색 도구
- `get_arxiv_tool()`: ArXiv 논문 검색 도구
- `execute_tool()`: 도구 실행 및 결과 반환
- `format_tool_result()`: 도구 결과 포맷팅
- `get_tools_map()`: 도구 맵핑 제공

#### `steaming/event_handlers.py`
- `StreamEventHandler` 클래스
- LangGraph 이벤트를 클라이언트 이벤트로 변환
- `StreamState`로 스트리밍 상태 관리

#### `steaming/streaming_utils.py`
- 스트리밍 관련 유틸리티 함수
- 도구 호출 정보 추출
- 도구 출력 파싱
- 연구 상태 메시지 생성

### API 모듈

#### `router.py`
- FastAPI 라우터 정의
- `/api/chat/stream`, `/api/sessions`, `/health` 엔드포인트

#### `service.py`
- `ChatService` 클래스
- 비즈니스 로직 처리
- 세션 관리 및 에이전트 실행
- `stream_conversation()`: SSE 스트리밍 대화 처리
- `_summarize_report()`: 보고서 요약 (writer 노드 완료 시 300자 이내로 요약)

#### `schemas.py`
- Pydantic 스키마 정의
- `ChatRequest`, `ChatResponse` 등

#### `session.py`
- `SessionManager` 클래스
- 세션별 대화 히스토리 관리
- 20개 이상 메시지 시 자동 요약
- 보고서 요약 저장: writer 노드 완료 시 긴 보고서를 요약하여 저장

#### `sse.py`
- SSE 응답 생성 유틸리티
- `create_sse_response()` 함수

### Core 모듈

#### `config.py`
- 환경 변수 로드
- `Config` 클래스로 설정 관리

#### `llm.py`
- LLM 초기화
- `SCOPING_LLM`, `RESEARCHER_LLM`, `WRITER_LLM` 정의

#### `logging.py`
- 로깅 설정
- JSON 형식 로그 파일 생성

## 🔧 개발 가이드

### 새로운 노드 추가

1. `app/agents/nodes/`에 새 노드 파일 생성
2. `AgentState`를 입력/출력으로 하는 함수 작성
3. `app/agents/graph.py`의 `graph_builder()`에 노드 추가:
   ```python
   builder.add_node("new_node", new_node_function)
   ```
4. 엣지 연결:
   ```python
   builder.add_edge("previous_node", "new_node")
   ```

### 새로운 도구 추가

1. `app/agents/nodes/research_tools.py`에 도구 정의:
   ```python
   @tool
   async def new_tool(query: str) -> str:
       """도구 설명"""
       # 도구 로직
       return result
   ```

2. `get_tools_map()`에 도구 추가:
   ```python
   return {
       "tavily_search": get_search_tool(),
       "arxiv": get_arxiv_tool(),
       "new_tool": get_new_tool(),  # 추가
   }
   ```

3. `execute_tool()`에 실행 로직 추가:
   ```python
   elif tool_name == "new_tool":
       tool = tools_map.get("new_tool")
       # 실행 로직
   ```

4. `researcher.py`의 `_build_research_graph()`에서 도구 바인딩:
   ```python
   new_tool = get_new_tool()
   tools = [search_tool, arxiv_tool, new_tool]
   ```

### 이벤트 핸들러 수정

`app/agents/steaming/event_handlers.py`의 `StreamEventHandler` 클래스에서:

1. 새로운 이벤트 타입 처리 메서드 추가:
   ```python
   async def handle_new_event(self, event: Dict) -> AsyncIterator[Dict]:
       # 이벤트 처리 로직
       yield {"type": "new_event", "data": ...}
   ```

2. `runner.py`의 `stream()` 메서드에서 이벤트 생성:
   ```python
   if event_type == "new_event":
       async for e in handler.handle_new_event(event):
           yield e
   ```

### 프롬프트 수정

`app/agents/prompts.py`에서 각 노드별 프롬프트 수정:

- `SCOPING_SYSTEM_PROMPT`: 요구사항 명확화 프롬프트
- `RESEARCH_SYSTEM_PROMPT`: 연구 프롬프트
- `WRITING_SYSTEM_PROMPT`: 보고서 작성 프롬프트

## 📝 로깅

로깅 설정은 `app/core/logging.py`에서 관리됩니다.

로그 파일:
- `logs/root.json`: JSON 형식 로그
- 일별 로그 파일 자동 생성 (예: `root.json.2026-01-01`)

로그 레벨:
- `INFO`: 일반 정보
- `WARNING`: 경고
- `ERROR`: 에러
- `DEBUG`: 디버그 (개발 환경)

## 🧪 테스트

```bash
# 테스트 실행 (추후 추가 예정)
pytest
```

## 🐛 문제 해결

### 포트 충돌

다른 포트 사용:
```bash
uvicorn app.main:app --reload --port 8001
```

### 환경 변수 로드 실패

`.env` 파일이 `backend/` 디렉토리에 있는지 확인하세요.

### 의존성 설치 오류

Python 버전 확인 (3.11 이상 권장):
```bash
python --version
```

가상 환경 사용 권장:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### LLM API 에러

- OpenAI API 키가 올바른지 확인
- API 사용량 및 한도 확인
- 네트워크 연결 확인

### 스트리밍 이벤트가 전송되지 않음

- LangGraph의 `astream_events`가 올바르게 호출되는지 확인
- `runner.py`의 `stream()` 메서드 확인
- 브라우저 개발자 도구에서 SSE 연결 확인

## 📚 참고 자료

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [LangChain 문서](https://python.langchain.com/)
- [Pydantic 문서](https://docs.pydantic.dev/)
- [Tavily API 문서](https://docs.tavily.com/)
- [ArXiv API 문서](https://arxiv.org/help/api)

