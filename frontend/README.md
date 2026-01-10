# AI 트렌드 분석 어시스턴트 - Frontend (React)

React + TypeScript + Vite로 구성된 프론트엔드 애플리케이션입니다.

## 기술 스택

- **React 18** - UI 라이브러리
- **TypeScript** - 타입 안정성
- **Vite** - 빌드 도구 및 개발 서버
- **React Router** - 클라이언트 사이드 라우팅
- **Marked** - 마크다운 파싱
- **Mermaid** - 다이어그램 렌더링

## 프로젝트 구조

```
frontend/
├── src/
│   ├── components/       # 재사용 가능한 컴포넌트
│   │   ├── InputSection.tsx
│   │   ├── IntroSection.tsx
│   │   ├── Message.tsx
│   │   ├── MessageList.tsx
│   │   └── Sidebar.tsx
│   ├── contexts/         # React Context (전역 상태)
│   │   ├── AuthContext.tsx
│   │   └── ChatContext.tsx
│   ├── hooks/            # 커스텀 Hook
│   │   └── useSSE.ts
│   ├── pages/            # 페이지 컴포넌트
│   │   ├── Chat.tsx
│   │   └── Landing.tsx
│   ├── types/            # TypeScript 타입 정의
│   │   └── index.ts
│   ├── utils/            # 유틸리티 함수
│   │   ├── api.ts
│   │   ├── env.ts
│   │   └── markdown.ts
│   ├── App.tsx           # 메인 App 컴포넌트
│   ├── main.tsx          # 진입점
│   ├── styles.css        # 전역 스타일
│   └── vite-env.d.ts     # Vite 환경 타입 정의
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## 환경 설정

### 1. 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성하고 API 베이스 URL을 설정합니다:

```bash
# .env
VITE_API_BASE_URL=http://localhost:8000
```

**중요:**
- 개발 환경에서는 `.env` 파일에 `VITE_API_BASE_URL`을 설정합니다.
- 프로덕션 환경에서 `.env` 파일이 없으면 자동으로 `window.location.origin`을 사용합니다 (nginx 프록시 환경).
- **코드 내에 localhost를 하드코딩하지 않습니다.**

### 2. 의존성 설치

```bash
npm install
```

## 개발 서버 실행

```bash
npm run dev
```

개발 서버가 `http://localhost:3000`에서 실행됩니다.

## 빌드

프로덕션 빌드:

```bash
npm run build
```

빌드된 파일은 `dist/` 폴더에 생성됩니다.

## 주요 기능

### 1. 인증 (AuthContext)

- 로그인/로그아웃 상태 관리
- localStorage를 사용한 세션 유지
- 사용자 정보 관리 (userId, userName)

### 2. 채팅 (ChatContext)

- Thread 목록 관리
- 현재 활성 Thread 관리
- 메시지 목록 관리

### 3. SSE 스트리밍 (useSSE Hook)

- Server-Sent Events를 사용한 실시간 스트리밍
- 스트림 취소 기능
- 에러 처리

### 4. 마크다운 렌더링

- Marked 라이브러리를 사용한 마크다운 파싱
- Mermaid 다이어그램 렌더링
- 코드 하이라이팅

## API 엔드포인트

모든 API 호출은 `src/utils/env.ts`에서 정의된 `API_BASE_URL`을 기반으로 합니다:

- `POST /api/chat/stream` - SSE 스트리밍 채팅
- `GET /api/users?name={name}` - 사용자 조회
- `POST /api/users` - 사용자 생성
- `GET /api/threads?user_id={user_id}` - Thread 목록 조회
- `POST /api/threads` - Thread 생성
- `GET /api/threads/{thread_id}/messages` - 메시지 조회

## 환경별 설정

### 개발 환경

`.env` 파일:
```
VITE_API_BASE_URL=http://localhost:8000
```

### 프로덕션 환경 (nginx 프록시)

`.env` 파일 없이 배포하면 자동으로 `window.location.origin`을 사용합니다.

nginx 설정 예시:
```nginx
location /api/ {
    proxy_pass http://backend:8000/api/;
}

location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
}
```

## 라이센스

MIT
