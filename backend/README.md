# Backend - AI 트렌드 분석 어시스턴트

FastAPI 기반 백엔드 서버로, LangGraph를 사용한 에이전트 워크플로우와 SSE 스트리밍을 제공합니다.

## 🛠 기술 스택

- **FastAPI**: 고성능 비동기 웹 프레임워크
- **LangGraph**: 에이전트 워크플로우 관리 및 상태 관리
- **LangChain**: LLM 통합 및 도구 사용
- **OpenAI**: GPT 모델 (gpt-4o, gpt-4o-mini)
- **Tavily**: 웹 검색 API
- **ArXiv**: 학술 논문 검색
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증

## 📁 프로젝트 구조

```
backend/
├── app/
│   ├── agents/              # 에이전트 관련 모듈
│   │   ├── event_handlers.py # 스트리밍 이벤트 핸들러
│   │   ├── graph.py         # LangGraph 그래프 정의
│   │   ├── runner.py        # 에이전트 실행기
│   │   ├── state.py         # 에이전트 상태 정의
│   │   ├── streaming.py     # 스트리밍 유틸리티
│   │   └── nodes/           # 에이전트 노드
│   │       ├── scoping.py   # 요구사항 명확화 노드
│   │       ├── researcher.py # 자료 수집 노드
│   │       └── writer.py    # 보고서 작성 노드
│   ├── api/                 # API 레이어
│   │   ├── router.py        # FastAPI 라우터
│   │   ├── service.py       # 비즈니스 로직
│   │   ├── schemas.py       # Pydantic 스키마
│   │   ├── session.py       # 세션 관리
│   │   └── sse.py           # SSE 유틸리티
│   ├── core/                # 핵심 설정
│   │   ├── config.py        # 환경 변수 설정
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
pip install -r requirements.txt
```

### 개발 서버 실행

```bash
uvicorn app.main:app --reload --port 8000
```

서버는 `http://localhost:8000`에서 실행됩니다.

### Docker로 실행

```bash
docker-compose up backend
```

## 📡 API 엔드포인트

### POST `/api/chat`

일반 채팅 요청 (비스트리밍)

**Request:**
```json
{
  "session_id": "optional-session-id",
  "user_message": "최근 AI 트렌드 분석해줘"
}
```

**Response:**
```json
{
  "assistant_message": "분석 결과...",
  "session_id": "session-id"
}
```

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

## 🏗 아키텍처

### 에이전트 워크플로우

LangGraph를 사용하여 다음 3단계 워크플로우를 구현:

1. **clarify_requirement** (`scoping.py`)
   - 사용자 요구사항 분석 및 명확화
   - 구조화된 출력으로 주제, 범위, 요구사항 추출

2. **researcher** (`researcher.py`)
   - 웹 검색 (Tavily) 및 논문 검색 (ArXiv)
   - 반복적 검색 전략으로 정보 수집
   - 수집된 정보를 findings로 정리

3. **writer** (`writer.py`)
   - 수집된 findings를 바탕으로 마크다운 보고서 생성
   - 구조화된 형식으로 최종 답변 생성

### 스트리밍 구조

**이벤트 핸들러** (`event_handlers.py`):
- `StreamEventHandler` 클래스가 각 이벤트 타입별 처리
- `StreamState`로 스트리밍 상태 관리
- LangGraph의 `astream_events`를 사용하여 실시간 이벤트 감지

**SSE 유틸리티** (`sse.py`):
- SSE 형식으로 이벤트 변환
- 에러 처리 포함

### 세션 관리

- `SessionManager`로 대화 세션 관리
- 대화가 20개 이상이면 자동 요약하여 컨텍스트 유지

## 🔧 개발 가이드

### 새로운 노드 추가

1. `app/agents/nodes/`에 새 노드 파일 생성
2. `AgentState`를 입력/출력으로 하는 함수 작성
3. `app/agents/graph.py`에 노드 추가 및 엣지 연결

### 이벤트 핸들러 수정

`app/agents/event_handlers.py`의 `StreamEventHandler` 클래스에서:
- 새로운 이벤트 타입 처리 메서드 추가
- 기존 핸들러 수정

### 스트리밍 이벤트 추가

1. `event_handlers.py`에서 새 이벤트 타입 처리
2. `runner.py`의 `stream()` 메서드에서 이벤트 생성
3. Frontend에서 해당 이벤트 타입 처리 추가

## 📝 로깅

로깅 설정은 `app/core/logging.py`에서 관리됩니다.

로그 파일:
- `logs/root.json`: JSON 형식 로그
- 일별 로그 파일 자동 생성

## 🧪 테스트

```bash
# 테스트 실행 (추후 추가 예정)
pytest
```

## 🐳 Docker

### 이미지 빌드

```bash
docker build -t research-agent-backend .
```

### 컨테이너 실행

```bash
docker run -p 8000:8000 --env-file .env research-agent-backend
```

## 📚 참고 자료

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [LangChain 문서](https://python.langchain.com/)

## 🔍 문제 해결

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

