# Frontend - Trend Agent UI

React + TypeScript 기반의 AI 트렌드 분석 에이전트 프론트엔드입니다.

## 📋 목차

- [아키텍처](#아키텍처)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [핵심 컴포넌트](#핵심-컴포넌트)
- [상태 관리](#상태-관리)
- [v1 대비 개선사항](#v1-대비-개선사항)
- [설치 및 실행](#설치-및-실행)
- [개발 가이드](#개발-가이드)

---

## 🏗️ 아키텍처

### 컴포넌트 구조

```
App (Router)
├── Landing Page (/)
│   └── 서비스 소개 + 시작하기 버튼
│
├── Threads Page (/chat)
│   ├── Sidebar (Thread 목록)
│   ├── IntroSection (사용 예시)
│   └── InputSection (메시지 입력)
│
└── Chat Page (/chat/:threadId)
    ├── Sidebar (Thread 목록)
    ├── MessageList
    │   ├── Message (user/assistant)
    │   ├── NodeStatus (노드 상태)
    │   ├── ResearchStatus (리서치 진행)
    │   └── ResearchFindings (출처 토글)
    └── InputSection (메시지 입력)
```

### 데이터 흐름

```
┌─────────────────────────────────────────────────────────────┐
│                     React Components                        │
│                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌───────────────┐  │
│  │ Landing │  │ Threads │  │  Chat   │  │  Components   │  │
│  │  Page   │  │  Page   │  │  Page   │  │               │  │
│  └────┬────┘  └────┬────┘  └────┬────┘  └───────┬───────┘  │
│       │            │            │                │          │
│       └────────────┴────────────┴────────────────┘          │
│                           │                                  │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │                   Contexts                            │   │
│  │  ┌─────────────────┐  ┌─────────────────┐            │   │
│  │  │   AuthContext   │  │   ChatContext   │            │   │
│  │  │   (userId)      │  │   (threads,     │            │   │
│  │  │                 │  │    messages)    │            │   │
│  │  └─────────────────┘  └─────────────────┘            │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
│  ┌────────────────────────▼─────────────────────────────┐   │
│  │                   Custom Hooks                        │   │
│  │  ┌────────────────────────────────────────────────┐  │   │
│  │  │                    useSSE                       │  │   │
│  │  │  • stream(): SSE 연결 및 이벤트 처리             │  │   │
│  │  │  • cancelStream(): 스트림 취소                  │  │   │
│  │  │  • isThreadStreaming(): 상태 확인              │  │   │
│  │  └────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                           │                                  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Utils (API)                            │
│  fetchThreads, fetchMessages, createThread, ...             │
└─────────────────────────────────────────────────────────────┘
                            │ HTTP / SSE
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend API                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ 기술 스택

| 카테고리 | 기술 | 버전 | 용도 |
|---------|------|------|------|
| **UI Library** | React | 18.2+ | 컴포넌트 기반 UI |
| **Language** | TypeScript | 5.2+ | 타입 안정성 |
| **Build Tool** | Vite | 5.0+ | 빠른 개발 서버 |
| **Routing** | React Router | 6.20+ | 클라이언트 라우팅 |
| **Markdown** | Marked.js | 11.1+ | 마크다운 파싱 |
| **Diagrams** | Mermaid.js | 10.6+ | 다이어그램 렌더링 |

---

## 📁 프로젝트 구조

```
frontend/
├── src/
│   ├── components/              # UI 컴포넌트
│   │   ├── InputSection.tsx     # 메시지 입력 영역
│   │   ├── IntroSection.tsx     # 시작 화면 (사용 예시)
│   │   ├── Message.tsx          # 개별 메시지
│   │   ├── MessageList.tsx      # 메시지 목록
│   │   ├── NodeStatus.tsx       # Agent 노드 상태
│   │   ├── ResearchFindings.tsx # 출처 정보 토글
│   │   ├── ResearchStatus.tsx   # 리서치 진행 상태
│   │   └── Sidebar.tsx          # Thread 목록 사이드바
│   │
│   ├── contexts/                # React Context
│   │   ├── AuthContext.tsx      # 인증 상태 관리
│   │   └── ChatContext.tsx      # 채팅 상태 관리
│   │
│   ├── hooks/                   # Custom Hooks
│   │   └── useSSE.ts            # SSE 스트리밍 훅
│   │
│   ├── pages/                   # 페이지 컴포넌트
│   │   ├── Landing.tsx          # 랜딩 페이지
│   │   ├── Threads.tsx          # 메인 페이지 (새 대화)
│   │   └── Chat.tsx             # 채팅 페이지
│   │
│   ├── types/                   # TypeScript 타입
│   │   └── index.ts             # 공통 타입 정의
│   │
│   ├── utils/                   # 유틸리티
│   │   ├── api.ts               # API 호출 함수
│   │   ├── env.ts               # 환경 변수
│   │   └── markdown.ts          # 마크다운 처리
│   │
│   ├── App.tsx                  # 앱 진입점 + 라우팅
│   ├── main.tsx                 # React 렌더링
│   └── styles.css               # 전역 스타일
│
├── public/                      # 정적 파일
├── index.html                   # HTML 템플릿
├── package.json                 # 의존성
├── tsconfig.json                # TypeScript 설정
└── vite.config.ts               # Vite 설정
```

---

## 🔧 핵심 컴포넌트

### 1. useSSE Hook

**역할:** Thread별 독립적인 SSE 스트리밍 관리

```typescript
const {
  streamingThreads,      // 현재 스트리밍 중인 Thread Set
  isThreadStreaming,     // 특정 Thread 스트리밍 여부
  error,                 // 에러 상태
  stream,                // 스트림 시작
  cancelStream,          // 특정 Thread 스트림 취소
  cancelAllStreams,      // 모든 스트림 취소
} = useSSE();
```

**핵심 기능:**
- Thread별 독립적인 AbortController 관리
- 자동 재연결 없이 깔끔한 정리
- 에러 핸들링

### 2. ChatContext

**역할:** 전역 채팅 상태 관리

```typescript
const {
  threads,            // Thread 목록
  setThreads,         // Thread 목록 설정
  currentThreadId,    // 현재 Thread ID
  setCurrentThreadId, // 현재 Thread 설정
  messages,           // 메시지 목록
  addMessage,         // 메시지 추가
  clearChat,          // 상태 초기화
} = useChat();
```

### 3. AuthContext

**역할:** 사용자 인증 상태 관리

```typescript
const {
  userId,             // 현재 사용자 ID
  setUserId,          // 사용자 ID 설정
  isLoading,          // 로딩 상태
} = useAuth();
```

### 4. MessageList

**역할:** 메시지 목록 + 스트리밍 상태 표시

**기능:**
- 사용자/어시스턴트 메시지 렌더링
- 스트리밍 중 실시간 상태 표시
- 조건부 자동 스크롤
- Research Findings 토글

### 5. IntroSection

**역할:** 사용 예시 및 시작 안내

**기능:**
- 클릭 가능한 예시 카드
- 서비스 사용법 안내
- 예시 클릭 시 자동 입력

---

## 📊 상태 관리

### Thread별 상태 분리

```
┌─────────────────────────────────────────────────────────┐
│                    App Level State                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ChatContext: threads, currentThreadId           │   │
│  │ AuthContext: userId                              │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Page Level State                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Chat.tsx:                                        │   │
│  │   • messages (local state)                       │   │
│  │   • streamingContent                             │   │
│  │   • nodeStatus, researchStatus, findings         │   │
│  │   • shouldAutoScroll                             │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Hook Level State                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │ useSSE:                                          │   │
│  │   • streamingThreads (Set<string>)               │   │
│  │   • streamStatesRef (Map<threadId, state>)       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### SSE 이벤트 처리 흐름

```typescript
// Chat.tsx - handleSSEEvent
const handleSSEEvent = useCallback((event: SSEEvent) => {
  switch (event.type) {
    case 'thread':
      // Thread 제목 업데이트
      loadThreadList();
      break;
      
    case 'node_start':
      // 노드 시작 상태 표시
      setNodeStatus({ name: event.node, status: 'in_progress' });
      break;
      
    case 'text_chunk':
      // 스트리밍 텍스트 추가
      setStreamingContent(prev => prev + event.content);
      break;
      
    case 'research_findings':
      // 리서치 결과 저장
      setFindings(event.findings);
      break;
      
    case 'final':
      // 최종 결과 처리
      addMessage({ role: 'assistant', message: event.state.answer, ... });
      setStreamingContent('');
      break;
  }
}, []);
```

---

## 🚀 v1 대비 개선사항

### 1. 프레임워크 현대화

| 항목 | v1 (Legacy) | v2 (현재) |
|------|-------------|-----------|
| 언어 | Vanilla JS | TypeScript |
| UI | 직접 DOM 조작 | React 컴포넌트 |
| 빌드 | 없음 (CDN) | Vite |
| 라우팅 | 단일 페이지 | React Router |

### 2. 타입 안정성

```typescript
// v2: 완전한 타입 정의
interface Message {
  thread_id: string;
  role: 'user' | 'assistant';
  message: string;
  timestamp?: string;
  ended_node?: string;
  findings?: Finding[];
}

interface SSEEvent {
  type: 'thread' | 'node_start' | 'text_chunk' | 'final' | ...;
  // type별 추가 필드
}
```

### 3. Thread별 독립 라우팅

```
v1: domain.com/ (단일 페이지, 모든 상태 전역)
v2: domain.com/chat/:threadId (Thread별 독립 페이지)
```

**장점:**
- Thread별 독립적인 상태 관리
- 뒤로가기/앞으로가기 지원
- URL 공유 가능
- 브라우저 히스토리 활용

### 4. 실시간 상태 표시

| 컴포넌트 | 기능 |
|----------|------|
| `NodeStatus` | 현재 실행 중인 Agent 노드 표시 |
| `ResearchStatus` | 리서치 진행 상황 (검색 쿼리, 결과) |
| `ResearchFindings` | 출처 정보 토글 표시 |

### 5. 조건부 자동 스크롤

```typescript
const handleScroll = useCallback(() => {
  const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
  // 하단 50px 이내면 자동 스크롤, 그렇지 않으면 비활성화
  setShouldAutoScroll(distanceFromBottom < 50);
}, []);
```

### 6. 응답 중지 기능

- 전송 버튼 → 중지 버튼 전환
- SSE 연결 끊기 + 백엔드 Task 취소
- 부분 응답 저장

### 7. 사용 예시 UI

- 클릭 가능한 예시 카드 4개
- 카드 클릭 시 자동 입력 및 전송
- 반응형 그리드 (데스크탑 2열, 모바일 1열)

---

## 🔧 설치 및 실행

### 로컬 개발

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build

# 프리뷰
npm run preview
```

### 환경 변수

```bash
# .env (선택사항)
VITE_API_BASE_URL=http://localhost:8000
```

---

## 📝 개발 가이드

### 새로운 컴포넌트 추가

1. `src/components/`에 `.tsx` 파일 생성
2. Props 타입 정의
3. 필요시 `src/types/index.ts`에 타입 추가

```typescript
// 예: src/components/MyComponent.tsx
import React from 'react';

interface MyComponentProps {
  title: string;
  onClick?: () => void;
}

export const MyComponent: React.FC<MyComponentProps> = ({ title, onClick }) => {
  return (
    <div onClick={onClick}>
      <h3>{title}</h3>
    </div>
  );
};
```

### 새로운 페이지 추가

1. `src/pages/`에 페이지 컴포넌트 생성
2. `src/App.tsx`에 Route 추가

```typescript
// App.tsx
<Routes>
  <Route path="/new-page" element={<NewPage />} />
</Routes>
```

### SSE 이벤트 타입 추가

1. `src/types/index.ts`에 이벤트 타입 추가
2. `src/pages/Chat.tsx`의 `handleSSEEvent`에 케이스 추가

```typescript
// types/index.ts
export interface MyNewEvent extends SSEEvent {
  type: 'my_new_event';
  data: string;
}

// Chat.tsx
case 'my_new_event':
  console.log('New event:', event.data);
  break;
```

### 스타일 가이드

- 전역 스타일: `src/styles.css`
- BEM-like 네이밍: `.component-name`, `.component-name__element`
- CSS 변수 활용: `var(--primary-color)`
- 반응형: `@media (max-width: 768px)`

---

## 📊 성능 최적화

### 적용된 최적화

| 기법 | 적용 위치 | 효과 |
|------|----------|------|
| `useCallback` | 이벤트 핸들러 | 불필요한 리렌더링 방지 |
| `useRef` | DOM 참조, 상태 추적 | 리렌더링 없이 값 유지 |
| Conditional Rendering | 상태 컴포넌트 | 불필요한 DOM 생성 방지 |
| Code Splitting | React Router | 초기 번들 크기 감소 |

### 향후 개선 가능

- [ ] React.memo로 컴포넌트 메모이제이션
- [ ] useMemo로 계산 결과 캐싱
- [ ] Intersection Observer로 무한 스크롤
- [ ] Service Worker로 오프라인 지원

---

**버전:** 2.0.0  
**최종 업데이트:** 2026년 1월
