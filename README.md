# 🔬 Trend Agent - AI 트렌드 분석 어시스턴트

LangGraph를 활용한 연구 및 기술 트렌드 분석 전문 AI 에이전트 서비스입니다.  
사용자의 요구사항을 이해하고, 최신 정보를 수집하여 전문적인 마크다운 형식의 종합 보고서를 생성합니다.

> 🔄 **v2.0** - 이 버전은 [legacy_v1](./legacy_v1/)에서 **대폭 개선된 버전**입니다.

## 📋 목차

- [서비스 소개](#서비스-소개)
- [v1 대비 개선사항](#v1-대비-개선사항)
- [기술 스택](#기술-스택)
- [아키텍처](#아키텍처)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 실행](#설치-및-실행)
- [사용 예시](#사용-예시)
- [API 문서](#api-문서)
- [향후 개선 계획](#향후-개선-계획)

---

## 🎯 서비스 소개

### 왜 만들었는가?

진로의 방향을 결정하거나 연구 주제를 선정할 때, 특정 기술의 최신 트렌드를 분석할 때 정보 수집 과정이 길고 어렵다는 경험에서 출발했습니다.

**해결하고자 하는 문제:**
- 📚 **정보의 양**: 웹과 학술 데이터베이스에 산재한 방대한 정보
- 🔍 **정보의 질**: 신뢰할 수 있는 출처와 최신성 확인의 어려움
- ⏰ **시간 소요**: 수동으로 정보를 수집하고 정리하는 데 드는 시간
- 📝 **전문성 요구**: 체계적인 보고서 작성 능력

### 핵심 기능

| 단계 | 기능 | 설명 |
|------|------|------|
| 1️⃣ | **요구사항 명확화** | 대화를 통해 연구 주제와 범위를 파악 |
| 2️⃣ | **정보 수집** | 웹 검색(Tavily) + 학술 논문(ArXiv) 자동 수집 |
| 3️⃣ | **보고서 작성** | 테이블, 다이어그램, 출처 포함 마크다운 보고서 생성 |

### 핵심 특징

- ✅ **LangGraph**: 서브그래프를 활용한 ReAct 패턴 구현
- ✅ **실시간 스트리밍**: SSE를 통한 연구 진행 상황 실시간 표시
- ✅ **Thread 관리**: 대화 기록 영구 저장 및 관리
- ✅ **응답 중지**: 언제든 응답 생성 취소 가능
- ✅ **출처 관리**: 모든 주장에 출처를 명시하여 신뢰성 확보

---

## 🚀 v1 대비 개선사항

### Frontend 개선

| 항목 | v1 (Legacy) | v2 (현재) |
|------|-------------|-----------|
| **프레임워크** | Vanilla JS | React 18 + TypeScript |
| **빌드 도구** | 없음 (CDN) | Vite |
| **상태 관리** | 전역 변수 | Context API + Custom Hooks |
| **라우팅** | 단일 페이지 | React Router (Thread별 URL) |
| **타입 안정성** | 없음 | TypeScript 완벽 지원 |

### Backend 개선

| 항목 | v1 (Legacy) | v2 (현재) |
|------|-------------|-----------|
| **데이터 저장** | 세션 기반 (메모리) | MongoDB 영구 저장 |
| **아키텍처** | 단일 모듈 | Repository + Service 패턴 |
| **Thread 관리** | 없음 | CRUD + 상태 관리 |
| **사용자 관리** | 없음 | User 시스템 |
| **백그라운드 처리** | 없음 | asyncio.Task + Queue 패턴 |

### UX/안정성 개선

| 개선 항목 | 설명 |
|----------|------|
| 🔄 **새로고침 안정성** | 새로고침해도 백그라운드에서 Agent 계속 실행, DB 저장 보장 |
| ⏹️ **응답 중지** | 중지 버튼 클릭 시 Agent 즉시 중단, 불필요한 API 비용 절약 |
| 📊 **실시간 상태** | 노드 상태, 리서치 진행 상황 실시간 표시 |
| 📜 **스마트 스크롤** | 조건부 자동 스크롤 (사용자 스크롤 시 비활성화) |
| 💾 **Findings 저장** | 출처 정보 DB에 영구 저장, 새로고침 후에도 확인 가능 |
| 🔒 **권한 관리** | Thread 소유자만 접근 가능 |

> 📝 상세 개선사항은 [IMPROVEMENTS.md](./IMPROVEMENTS.md) 참조

---

## 🛠️ 기술 스택

### Backend
- **FastAPI** `0.128.0` - 고성능 비동기 웹 프레임워크
- **LangGraph** `1.0.5` - 에이전트 워크플로우 관리
- **LangChain** `1.2.0` - LLM 통합 및 도구 사용
- **LangChain OpenAI** `1.1.6` - OpenAI 통합
- **LangChain Tavily** `0.2.16` - Tavily 검색 통합
- **MongoDB** `4.16.0` (pymongo) - 데이터 영구 저장
- **Motor** (async driver) - 비동기 MongoDB 드라이버
- **OpenAI** `2.14.0` - GPT 모델 API (gpt-4o, gpt-4o-mini)
- **Tavily** - 웹 검색 API
- **ArXiv** `2.3.1` - 학술 논문 검색
- **Pydantic** `2.12.5` - 데이터 검증 및 직렬화
- **Uvicorn** `0.40.0` - ASGI 서버

### Frontend
- **React** `18.2.0` - UI 라이브러리
- **TypeScript** `5.2.2` - 타입 안정성
- **Vite** `5.0.8` - 빠른 빌드 도구
- **React Router DOM** `6.20.1` - 클라이언트 라우팅
- **Marked** `11.1.1` - 마크다운 파싱
- **Mermaid** `10.6.1` - 다이어그램 렌더링

### Infrastructure
- **Docker & Docker Compose** - 컨테이너화 및 배포
- **Nginx** - 리버스 프록시 및 정적 파일 서빙
- **AWS EC2** - 클라우드 배포
- **Python** `3.11+` - 백엔드 런타임
- **Node.js** `18+` - 프론트엔드 빌드

---

## 🏗️ 아키텍처

### 전체 워크플로우

```
사용자 입력
    ↓
[clarify_requirement] → 요구사항 명확화
    ↓ (is_clarified = True)
[researcher] → 정보 수집 (ReAct 패턴)
    ├─ agent_node: LLM이 도구 선택
    ├─ tools_node: 도구 실행 (웹/논문 검색)
    └─ 반복 (최대 3회)
    ↓
[writer] → 보고서 작성
    ↓
최종 보고서 반환
```

### 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐ │
│  │ Landing │  │ Threads │  │  Chat   │  │ Components      │ │
│  │  Page   │  │  Page   │  │  Page   │  │ (SSE, Status)   │ │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────────┬────────┘ │
│       └────────────┴────────────┴────────────────┘          │
│                           │                                  │
│           Context API + Custom Hooks (useSSE)               │
└─────────────────────────────────────────────────────────────┘
                            │ HTTP / SSE
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                         Nginx                               │
│                (Reverse Proxy + Static)                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                     API Layer                         │   │
│  │  ┌────────────────┐  ┌────────────────┐              │   │
│  │  │  Chat Router   │  │  Users Router  │              │   │
│  │  └───────┬────────┘  └───────┬────────┘              │   │
│  │          │                    │                       │   │
│  │  ┌───────┴────────────────────┴───────┐              │   │
│  │  │            Service Layer           │              │   │
│  │  │  (ChatService, ChatThreadService)  │              │   │
│  │  └───────────────┬────────────────────┘              │   │
│  │                  │                                    │   │
│  │  ┌───────────────┴────────────────────┐              │   │
│  │  │          Repository Layer          │              │   │
│  │  │  (ChatThreadRepo, ChatMessageRepo) │              │   │
│  │  └───────────────┬────────────────────┘              │   │
│  └──────────────────┼────────────────────────────────────┘   │
│                     │                                        │
│  ┌──────────────────┼────────────────────────────────────┐   │
│  │              Agents Layer                              │   │
│  │  ┌───────────────┴───────────────────┐                │   │
│  │  │          LangGraph App            │                │   │
│  │  │  ┌─────────┐ ┌──────────┐ ┌─────┐ │                │   │
│  │  │  │ Scoping │→│Researcher│→│Writer│ │                │   │
│  │  │  └─────────┘ └────┬─────┘ └─────┘ │                │   │
│  │  │                   │               │                │   │
│  │  │            ┌──────┴──────┐        │                │   │
│  │  │            │ ReAct Loop  │        │                │   │
│  │  │            │ (SubGraph)  │        │                │   │
│  │  │            └─────────────┘        │                │   │
│  │  └───────────────────────────────────┘                │   │
│  └────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                        MongoDB                              │
│     ┌──────────────┐  ┌────────────────┐  ┌─────────────┐   │
│     │ chat_threads │  │ chat_messages  │  │   users     │   │
│     └──────────────┘  └────────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 프로젝트 구조

```
.
├── backend/                    # FastAPI 백엔드
│   ├── app/
│   │   ├── agents/            # LangGraph 에이전트
│   │   │   ├── nodes/         # 노드 구현 (scoping, researcher, writer)
│   │   │   ├── streaming/     # SSE 스트리밍 핸들러
│   │   │   ├── graph.py       # LangGraph 그래프 정의
│   │   │   └── runner.py      # 에이전트 실행기
│   │   ├── api/               # API 레이어
│   │   │   ├── chat/          # 채팅 API (CRUD, SSE)
│   │   │   └── users/         # 사용자 API
│   │   ├── core/              # 핵심 설정 (config, llm, logging)
│   │   ├── db/                # 데이터베이스 (MongoDB)
│   │   └── main.py
│   └── README.md              # 백엔드 상세 문서
│
├── frontend/                   # React 프론트엔드
│   ├── src/
│   │   ├── components/        # UI 컴포넌트
│   │   ├── contexts/          # React Context (Auth, Chat)
│   │   ├── hooks/             # Custom Hooks (useSSE)
│   │   ├── pages/             # 페이지 (Landing, Threads, Chat)
│   │   └── utils/             # 유틸리티 (API, markdown)
│   └── README.md              # 프론트엔드 상세 문서
│
├── nginx/                      # Nginx 설정
├── docs/                       # 추가 문서
├── legacy_v1/                  # 이전 버전 (참고용)
├── IMPROVEMENTS.md             # 상세 개선사항 문서
└── docker-compose.*.yml        # Docker 설정
```

---

## 🚀 설치 및 실행

### 사전 요구사항

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- MongoDB
- OpenAI API Key
- Tavily API Key

### 환경 변수 설정

```bash
# backend/.env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=trend_agent_db
```

### Docker로 실행 (권장)

```bash
# 개발 환경
docker-compose -f docker-compose.dev.yml up -d

# 프로덕션 환경
docker-compose -f docker-compose.prod.yml up -d
```

### 로컬 개발 환경

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (별도 터미널)
cd frontend
npm install
npm run dev
```

**접속 주소:**
- Frontend: http://localhost:5173 (dev) / http://localhost (docker)
- Backend API: http://localhost:8000/api

---

## 💡 사용 예시

### 질문 예시

```
"2026년 AI 에이전트 시장 전망과 주요 트렌드"
"최근 mRNA 백신 기술 발전 동향"
"고체 배터리 기술의 최신 연구 동향"
```

### 에이전트 동작 흐름

1. **요구사항 명확화**: 주제와 범위 확인
2. **정보 수집**: 
   - 웹 검색: "AI 에이전트 최신 트렌드 2026"
   - 논문 검색: "AI agent recent trends"
3. **보고서 작성**: 수집된 정보 기반 종합 보고서 생성

---

## 📡 API 문서

### 주요 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/chat/stream` | SSE 스트리밍 채팅 |
| GET | `/api/chat/threads` | Thread 목록 조회 |
| POST | `/api/chat/threads` | Thread 생성 |
| GET | `/api/chat/threads/{id}/messages` | 메시지 조회 |
| POST | `/api/chat/cancel-task` | 백그라운드 작업 취소 |

자세한 API 문서는 `http://localhost:8000/docs` (Swagger UI) 참조

---

## 🔮 향후 개선 계획

### 단기 개선
- [ ] WebSocket 전환 (양방향 통신)
- [ ] Progress Bar 추가 (진행률 시각화)
- [ ] 캐싱 시스템 (동일 질문 빠른 응답)

### 중장기 개선
- [ ] 멀티모달 지원 (이미지, PDF 분석)
- [ ] 협업 기능 (Thread 공유)
- [ ] 커스텀 프롬프트 설정
- [ ] 성능 모니터링 대시보드

---

## 📚 참고 자료

- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [React 문서](https://react.dev/)

---

**버전:** 2.0.0  
**최종 업데이트:** 2026년 1월
