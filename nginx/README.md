# Nginx 설정 가이드

## 파일 구성

- `nginx.conf.dev` - 개발용 설정 (HTTP only)
- `nginx.conf.prod` - 프로덕션용 설정 (HTTPS 포함)
- `nginx.conf` - 프로덕션용 (호환성 유지, EC2용)
- `Dockerfile` - 개발용 Dockerfile (nginx.conf.dev 사용)
- `Dockerfile.prod` - 프로덕션용 Dockerfile (nginx.conf.prod 사용)

## 설정 파일 차이

### nginx.conf.dev (로컬 개발용)
- ✅ HTTP only (포트 80)
- ✅ SSL 인증서 불필요
- ✅ localhost 접속
- ✅ 빠른 테스트

### nginx.conf.prod (EC2 프로덕션용)
- ✅ HTTPS (포트 443)
- ✅ SSL 인증서 필요
- ✅ 도메인 접속 (chwlabs.dev)
- ✅ HTTP → HTTPS 리다이렉트

## 개발 환경 (권장)

호스트에서 React를 빌드하고 결과물을 마운트합니다.

### 1. React 빌드

```bash
cd frontend
npm install
npm run build
```

### 2. Docker Compose 실행

```bash
# 프로젝트 루트에서
docker-compose up --build
```

이 방법은:
- ✅ 빌드 속도가 빠름 (호스트의 node_modules 캐시 활용)
- ✅ 핫 리로드 가능 (개발 중 빌드만 다시 실행)
- ✅ 디버깅 용이

## 프로덕션 환경

React 빌드를 Docker 이미지에 포함합니다.

### 프로덕션 빌드 및 실행

```bash
# 프로젝트 루트에서
docker-compose -f docker-compose.prod.yml up --build
```

이 방법은:
- ✅ 단일 이미지로 배포 가능
- ✅ 호스트에 Node.js 설치 불필요
- ✅ 일관된 빌드 환경
- ⚠️ 빌드 시간이 더 오래 걸림

## Nginx 설정 상세

### API 프록시

```nginx
location /api/ {
    proxy_pass http://backend/;
    # SSE를 위한 설정
    proxy_buffering off;
    proxy_read_timeout 300s;
}
```

### SPA 라우팅

```nginx
location / {
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
}
```

React Router의 모든 경로가 `index.html`로 라우팅됩니다.

### 정적 파일 캐싱

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

빌드된 자산 파일은 1년간 캐싱됩니다.

## SSL/TLS 설정

프로덕션에서 HTTPS를 사용하려면:

1. Let's Encrypt 인증서 발급
2. `nginx.conf`의 `server_name` 수정
3. 인증서 경로 확인

```nginx
ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
```

## 로컬 개발 (HTTP Only)

개발 환경에서 HTTPS가 필요 없다면 `nginx.conf`를 수정:

```nginx
server {
    listen 80;
    
    # API 프록시
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_buffering off;
    }
    
    # SPA 라우팅
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
}
```

## 트러블슈팅

### 1. 502 Bad Gateway

**원인**: 백엔드 서버에 연결할 수 없음

**해결**:
```bash
# 백엔드 상태 확인
docker-compose logs backend

# 네트워크 확인
docker network ls
docker network inspect agent-260104_app-network
```

### 2. 404 Not Found (React 라우팅)

**원인**: `try_files` 설정 누락

**해결**: `nginx.conf`에 다음 확인
```nginx
try_files $uri $uri/ /index.html;
```

### 3. API 호출 실패

**원인**: 프록시 설정 오류

**해결**: 브라우저 개발자 도구에서 네트워크 확인
- `/api/users` → `http://backend:8000/api/users`로 프록시되는지 확인

### 4. 빌드 파일이 없음

**원인**: `frontend/dist` 폴더가 비어있음

**해결**:
```bash
cd frontend
npm run build
ls -la dist/  # 파일 확인
```

## 성능 최적화

### 1. Gzip 압축 활성화

`nginx.conf`에 추가:
```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
gzip_min_length 1000;
```

### 2. 정적 파일 캐싱

이미 설정되어 있음:
```nginx
expires 1y;
add_header Cache-Control "public, immutable";
```

### 3. HTTP/2 활성화

이미 설정되어 있음:
```nginx
listen 443 ssl http2;
```

## 추가 참고

- React Router: https://reactrouter.com/
- Nginx 공식 문서: https://nginx.org/en/docs/
- Let's Encrypt: https://letsencrypt.org/
