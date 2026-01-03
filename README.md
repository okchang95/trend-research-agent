# AI 트렌드 분석 어시스턴트

최신 기술 트렌드와 연구 동향을 분석하여 종합 보고서를 제공하는 AI 어시스턴트입니다.

## 🚀 주요 기능

- **요구사항 명확화**: 대화를 통해 분석하고 싶은 주제를 명확히 파악
- **자료 수집**: 웹 검색과 학술 논문 검색을 통해 최신 정보를 수집
- **보고서 작성**: 수집된 자료를 바탕으로 체계적인 마크다운 보고서를 생성
- **실시간 스트리밍**: SSE(Server-Sent Events)를 통한 실시간 진행 상황 표시

## 📁 프로젝트 구조

```
.
├── backend/          # FastAPI 백엔드 서버
├── frontend/         # 정적 웹 프론트엔드
├── nginx/            # Nginx 설정
├── docs/             # 프로젝트 문서
└── docker-compose.yml # Docker Compose 설정
```

## 🛠 기술 스택

### Backend
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **LangGraph**: 에이전트 워크플로우 관리
- **LangChain**: LLM 통합 및 도구 사용
- **OpenAI**: GPT 모델 사용
- **Tavily**: 웹 검색 API
- **ArXiv**: 학술 논문 검색

### Frontend
- **Vanilla JavaScript**: 모듈화된 순수 JavaScript
- **Marked.js**: 마크다운 파싱
- **Mermaid.js**: 다이어그램 렌더링
- **SSE**: 실시간 스트리밍 통신

## 🚀 빠른 시작

### 사전 요구사항

- Docker & Docker Compose
- Python 3.11+ (로컬 개발 시)
- Node.js (프론트엔드 개발 시, 선택사항)

### 환경 변수 설정

`backend/.env` 파일을 생성하고 다음 환경 변수를 설정하세요:

```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
LANGCHAIN_TRACING_V2=false
LANGSMITH_API_KEY=
LANGSMITH_ENDPOINT=
LANGSMITH_PROJECT=
```

### Docker Compose로 실행

```bash
# 전체 스택 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 종료
docker-compose down
```

서비스는 다음 주소에서 접근 가능합니다:
- Frontend: http://localhost
- Backend API: http://localhost/api

### 로컬 개발

#### Backend 실행

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

자세한 내용은 [backend/README.md](./backend/README.md)를 참조하세요.

#### Frontend 실행

```bash
cd frontend
# Python HTTP 서버 사용
python -m http.server 8080

# 또는 serve.sh 스크립트 사용
./serve.sh
```

자세한 내용은 [frontend/README.md](./frontend/README.md)를 참조하세요.

## 📖 사용 방법

1. 웹 브라우저에서 프론트엔드 접속
2. 입력창에 분석하고 싶은 주제 입력 (예: "최근 AI 트렌드")
3. 시스템이 자동으로:
   - 요구사항을 명확히 파악
   - 웹 검색 및 논문 검색 수행
   - 종합 보고서 생성
4. 실시간으로 진행 상황 확인 가능

## 🏗 아키텍처

### 에이전트 워크플로우

1. **clarify_requirement**: 사용자 요구사항 명확화
2. **researcher**: 웹 검색 및 논문 검색을 통한 자료 수집
3. **writer**: 수집된 자료를 바탕으로 보고서 작성

### 스트리밍 구조

- **Backend**: LangGraph의 `astream_events`를 사용하여 노드별 이벤트 스트리밍
- **Frontend**: SSE를 통해 실시간으로 진행 상황 수신 및 UI 업데이트

## 📚 문서

- [Backend 문서](./backend/README.md)
- [Frontend 문서](./frontend/README.md)
- [프로젝트 사양서](./docs/specs.md)
- [개발 가이드](./docs/planning.md)

## 🔧 개발

### 코드 구조

프로젝트는 모듈화된 구조로 설계되어 있습니다:

- **Backend**: 이벤트 핸들러, 스트리밍 유틸리티, API 라우터 등으로 분리
- **Frontend**: SSE 클라이언트, 이벤트 핸들러, UI 업데이트, 마크다운 처리 등으로 모듈화

### 리팩토링

최근 대규모 리팩토링을 통해 코드 가독성과 유지보수성을 크게 향상시켰습니다:

- Backend: 이벤트 핸들러를 별도 모듈로 분리
- Frontend: 899줄의 단일 파일을 여러 모듈로 분리

## 📝 라이선스

이 프로젝트는 개인 프로젝트입니다.

## 🤝 기여

이슈 및 개선 사항은 이슈 트래커를 통해 제안해주세요.

