
5. 레이어별 설계 포인트 정리
    1) Product / Scope Layer
        - 범용 에이전트 vs **도메인 특화 에이전트**
        - 범용 엔진 + **도메인 가드레일** vs 완전 도메인 고정 에이전트
        - Open Deep Research 클론 구조 vs ODR-lite 재설계 구조
    2) Interaction / UX Layer
        - **싱글턴 에이전트** vs 멀티턴 에이전트
        - 외부 싱글턴 UX vs 내부 멀티턴 리서치 루프
        - **실시간 SSE 스트리밍** vs HTTP Polling 기반 상태/로그 조회
        - 로그 파일 tail 기반 관측 vs **에이전트 이벤트 로그 기반 관측**
    3) Frontend / Presentation Layer
        - Streamlit UI vs **Vanilla JS + HTML UI**
        - 서버 내 UI 실행 vs **서버-클라이언트 분리 UI**
    4) API / Delivery Layer
        - FastAPI 단독 실행 vs FastAPI + UI 분리
        - 단일 프로세스 실행 vs 분리 프로세스(FastAPI ↔ UI)
    5) Orchestration / Agent Runtime Layer (LangGraph 중심)
        - 싱글턴 그래프 vs 멀티턴 그래프(루프/분기)
        - OpenDR 클론 플로우 vs 품질 게이트/리페어 루프 포함 플로우
        - 에이전트 이벤트 기반 관측 vs 일반 서버 로그 기반 관측
    6) Tooling / Integration Layer
        - 직접 툴 구현 vs MCP 연동 구조
        - 내부 툴 중심 vs 외부 API 중심
    7) Data Sourcing / Retrieval Layer
        - 논문 아카이브 API 중심 vs 웹 검색 API 중심
        - 스크래핑 기반 KB vs API 기반 온디맨드 수집
        - 논문 근거 중심 vs 웹 트렌드 신호 중심
    8) Knowledge / Context Management Layer
        - 영구 Knowledge Base vs 세션 단위 임시 Knowledge Base
        - 정식 RAG(Vector DB) vs Evidence Bundle 기반 생성
        - 데이터베이스 사용 vs 메모리(In-memory) 기반
        - 체크포인트 저장 vs 완전 휘발 실행
    9) Infrastructure / Edge Layer
        - FastAPI 정적 파일 서빙 vs Nginx 정적 파일 서빙
        - Nginx 리버스 프록시 vs Route53 + ELB(ALB)
        - EC2 단일 인스턴스 vs 로드밸런서 전제 구조
        - 도메인 미구매 vs 도메인 구매 후 연결