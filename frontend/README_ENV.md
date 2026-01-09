# 환경 변수 설정 가이드

## .env 파일

`frontend/.env` 파일에 환경 변수를 설정할 수 있습니다.

### 현재 지원하는 환경 변수

- `API_BASE_URL` 또는 `VITE_API_BASE_URL`: API 서버의 기본 URL
  - 둘 다 지원합니다 (더 간단한 `API_BASE_URL` 권장)
  - 개발 환경: `.env` 파일에 `API_BASE_URL=http://localhost:8000` 설정
  - 프로덕션: `.env` 파일에 설정하지 않으면 자동으로 `window.location.origin` 사용 (nginx 프록시)

## 사용 방법

### 1. .env 파일 생성 및 수정

```bash
# frontend/.env 파일 생성
# 개발 환경에서만 설정 (로컬 개발 시)
API_BASE_URL=http://localhost:8000

# 프로덕션에서는 설정하지 않음 (자동으로 window.location.origin 사용)
# API_BASE_URL=
```

### 2. 환경 변수 주입 스크립트 실행

`.env` 파일을 수정한 후, HTML 파일에 환경 변수를 주입하려면:

```bash
cd frontend
node inject-env.js
```

이 스크립트는 `.env` 파일을 읽어서 `index.html`과 `landing.html`에 환경 변수를 자동으로 주입합니다.

### 3. JavaScript에서 사용

JavaScript 파일(`app.js`, `landing.js`)에서는 다음과 같이 사용합니다:

```javascript
// window.__ENV__ 객체에서 환경 변수 읽기
// .env에 설정되어 있으면 사용, 없으면 window.location.origin 사용 (프로덕션)
const API_BASE_URL = window.__ENV__?.API_BASE_URL || window.location.origin;
```

## 자동화

개발 시 매번 스크립트를 실행하는 것이 번거롭다면, 파일 감시(watch) 스크립트를 사용하거나 빌드 프로세스에 통합할 수 있습니다.

## 참고

- `.env` 파일은 Git에 커밋하지 않는 것을 권장합니다 (`.gitignore`에 추가)
- 프로덕션 환경에서는 빌드 시점에 환경 변수를 주입하는 것이 좋습니다
