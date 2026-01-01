# 연구/기술 트렌드 리서치 에이전트

연구 주제나 기술 트렌드 조사를 자동화하는 AI 에이전트입니다. LangGraph를 기반으로 사용자의 질문을 분석하고, Arxiv와 Tavily를 통해 관련 정보를 수집한 후, 전문적인 마크다운 형식의 리포트를 생성합니다.

## 주요 기능

- **의도 분석**: 사용자 질문의 의도를 자동으로 분석
- **데이터 수집**: 
  - Arxiv에서 최신 논문 검색
  - Tavily를 통한 웹 검색
- **리포트 생성**: 수집된 데이터를 바탕으로 마크다운 형식의 전문 리포트 생성
- **실시간 스트리밍**: SSE(Server-Sent Events)를 통한 중간 결과 실시간 표시

## 아키텍처

### 백엔드
- **FastAPI**: RESTful API 서버
- **LangGraph**: 에이전트 워크플로우 관리
- **LangChain**: LLM 통합 및 프롬프트 관리

### 프론트엔드
- **Vanilla JavaScript + HTML**: 경량 웹 인터페이스
- **SSE**: 실시간 스트리밍 지원

### 에이전트 구조

```
START → intent_analysis → data_collector → generate_response → END
```

1. **intent_analysis**: 사용자 메시지의 의도 분석
2. **data_collector**: Arxiv와 Tavily를 통한 컨텍스트 수집
3. **generate_response**: 마크다운 형식의 최종 리포트 생성

## 설치 및 실행

### 필수 요구사항

- Python 3.13+
- OpenAI API Key
- Tavily API Key (선택사항, 없으면 Arxiv만 사용)

### 1. 저장소 클론

```bash
git clone <repository-url>
cd agent-260104
```

### 2. Conda 가상 환경 생성 및 활성화

```bash
conda create -n research-agent python=3.13 -y
conda activate research-agent
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key  # 선택사항
```

### 5. 서버 실행

#### 방법 1: 직접 실행 (Conda 환경)

```bash
conda activate research-agent
uvicorn app.main:app --reload --port 8000
```

서버는 `http://localhost:8000`에서 실행됩니다.

#### 방법 2: Docker 사용

```bash
# Docker 이미지 빌드
docker build -t research-agent .

# Docker 컨테이너 실행
docker run -d \
  --name research-agent \
  -p 8000:8000 \
  --env-file .env \
  research-agent
```

서버는 `http://localhost:8000`에서 실행됩니다.

**참고**: 프론트엔드는 FastAPI에서 자동으로 서빙됩니다. 별도 서버 실행이 필요 없습니다.

## API 엔드포인트

### POST `/agent`
동기 실행 (기존 호환성 유지)

**Request:**
```json
{
  "user_message": "quantum computing trends"
}
```

**Response:**
```json
{
  "result_state": {
    "user_message": "quantum computing trends",
    "intent": "research",
    "intent_analysis_reason": "...",
    "data_collection_result": "...",
    "response": "# 마크다운 리포트..."
  }
}
```

### POST `/agent/stream`
SSE를 통한 스트리밍 실행

**Request:**
```json
{
  "user_message": "quantum computing trends"
}
```

**Response:** Server-Sent Events 스트림

각 노드 완료 시 이벤트가 전송됩니다:
- `node_complete`: 노드 실행 완료
- `final`: 최종 상태
- `error`: 오류 발생

### GET `/health`
서버 상태 확인

**Response:**
```json
{
  "status": "ok"
}
```

## 사용법

1. 브라우저에서 `http://localhost:8000` 접속 (FastAPI가 프론트엔드도 함께 서빙)
2. 검색창에 질문 입력 (예: "quantum computing trends", "AI research trends 2024")
3. 검색 버튼 클릭 또는 Enter 키 입력
4. 실시간으로 각 노드의 실행 상태 확인
5. 최종 리포트 확인 (마크다운 형식)

## 프로젝트 구조

```
agent-260104/
├── app/
│   ├── agent/              # 에이전트 로직
│   │   ├── nodes/          # 노드 구현
│   │   │   ├── intent_analysis.py
│   │   │   ├── data_collector.py
│   │   │   └── generate_response.py
│   │   ├── graph.py        # LangGraph 구성
│   │   ├── runner.py       # 에이전트 실행기
│   │   ├── state.py        # 상태 정의
│   │   └── llm.py          # LLM 설정
│   ├── api/                # API 라우터 및 서비스
│   │   ├── router.py
│   │   ├── service.py
│   │   └── schemas.py
│   ├── core/               # 핵심 설정
│   │   ├── config.py       # 환경 변수 관리
│   │   └── logging.py      # 로깅 설정
│   └── main.py             # FastAPI 앱 진입점
├── ui/                     # 프론트엔드
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── serve.sh
├── docs/                   # 문서
├── requirements.txt         # Python 의존성
└── README.md
```

## 기술 스택

### 백엔드
- **FastAPI**: 웹 프레임워크
- **LangGraph**: 에이전트 워크플로우
- **LangChain**: LLM 통합
- **OpenAI GPT-4o-mini**: LLM 모델
- **ArxivLoader**: 논문 검색
- **Tavily API**: 웹 검색

### 프론트엔드
- **Vanilla JavaScript**: 클라이언트 로직
- **Marked.js**: 마크다운 렌더링
- **SSE**: 실시간 스트리밍

## 로깅

각 노드의 실행 결과는 상세하게 로깅됩니다:

- `[Intent Analysis]`: 의도 분석 결과
- `[Data Collector]`: 데이터 수집 결과 (Arxiv, Tavily)
- `[Generate Response]`: 리포트 생성 결과

로그는 `logs/root.json`에 JSON 형식으로 저장됩니다.

## 개발

### 로컬 개발

1. 코드 수정 시 FastAPI 서버가 자동으로 리로드됩니다 (`--reload` 옵션)
2. 프론트엔드는 브라우저에서 새로고침하면 변경사항이 반영됩니다

### 테스트

각 노드는 독립적으로 테스트할 수 있습니다:

```bash
# intent_analysis 테스트
python -m app.agent.nodes.intent_analysis

# data_collector 테스트
python -m app.agent.nodes.data_collector

# generate_response 테스트
python -m app.agent.nodes.generate_response
```

## 라이선스

이 프로젝트는 개인 프로젝트입니다.

## 기여

이슈나 개선사항이 있으면 이슈를 등록해주세요.

