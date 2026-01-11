# Nginx 설정 파일 가이드

## 📁 파일 구조

```
nginx/
├── nginx.conf.dev       # 로컬 개발용 (HTTP only)
├── nginx.conf.prod      # EC2 프로덕션용 (HTTPS)
├── nginx.conf           # nginx.conf.prod 복사본 (호환성)
├── Dockerfile           # 개발용 (nginx.conf.dev 사용)
└── Dockerfile.prod      # 프로덕션용 (nginx.conf.prod 사용)
```

## 🔧 설정 파일 차이

### nginx.conf.dev (로컬 개발)

**특징:**
- ✅ HTTP only (포트 80)
- ✅ SSL 인증서 불필요
- ✅ `server_name localhost`
- ✅ 간단한 설정

**사용 환경:**
- 로컬 PC (Docker Desktop)
- 개발 서버 (테스트용)

**접속 방법:**
```bash
http://localhost
```

### nginx.conf.prod (EC2 프로덕션)

**특징:**
- ✅ HTTPS (포트 443)
- ✅ HTTP → HTTPS 리다이렉트
- ✅ SSL 인증서 필요 (/etc/letsencrypt)
- ✅ `server_name chwlabs.dev`
- ✅ 보안 강화 설정

**사용 환경:**
- EC2 인스턴스
- 실제 서비스 배포

**접속 방법:**
```bash
https://chwlabs.dev
```

## 🚀 사용 방법

### 로컬 개발 (자동)

```bash
# docker-compose.yml은 자동으로 nginx.conf.dev 사용
docker-compose up -d
```

`Dockerfile`이 자동으로 `nginx.conf.dev`를 복사합니다.

### EC2 프로덕션 (자동)

```bash
# docker-compose.prod.yml은 자동으로 nginx.conf.prod 사용
docker-compose -f docker-compose.prod.yml up -d
```

`Dockerfile.prod`가 자동으로 `nginx.conf.prod`를 복사합니다.

## 🔐 SSL 인증서 설정 (EC2만)

### 1. Let's Encrypt 인증서 발급

```bash
# Certbot 설치
sudo apt-get install certbot

# 인증서 발급
sudo certbot certonly --standalone -d chwlabs.dev

# 인증서 위치 확인
ls -la /etc/letsencrypt/live/chwlabs.dev/
```

### 2. 인증서 파일 확인

필수 파일:
- `fullchain.pem` - 전체 인증서 체인
- `privkey.pem` - 개인 키

### 3. 자동 갱신 설정

```bash
# crontab 편집
sudo crontab -e

# 매월 1일 새벽 3시에 갱신
0 3 1 * * certbot renew --quiet && docker-compose restart nginx
```

## 🔄 설정 변경 방법

### nginx.conf.dev 수정

```bash
# 1. 파일 수정
vi nginx/nginx.conf.dev

# 2. nginx 재시작
docker-compose restart nginx
```

### nginx.conf.prod 수정

```bash
# 1. 파일 수정 (EC2에서)
vi nginx/nginx.conf.prod

# 2. nginx 재빌드 및 재시작
docker-compose -f docker-compose.prod.yml up --build -d nginx
```

## 🐛 트러블슈팅

### 문제: nginx가 계속 재시작됨

**원인:** SSL 인증서 파일을 찾을 수 없음

**해결:** 
```bash
# 로컬에서 실행 시 nginx.conf.dev 사용하는지 확인
docker exec research-agent-nginx cat /etc/nginx/conf.d/default.conf

# "listen 80"만 있고 "listen 443 ssl"이 없어야 함
```

### 문제: 502 Bad Gateway

**원인:** 백엔드 컨테이너 미실행 또는 연결 실패

**해결:**
```bash
# 백엔드 상태 확인
docker-compose ps backend

# 백엔드 로그 확인
docker-compose logs backend

# 네트워크 확인
docker network inspect agent-260104_app-network
```

### 문제: Let's Encrypt 인증서 오류 (EC2)

**원인:** 도메인 DNS 설정 오류 또는 포트 80/443 미개방

**해결:**
```bash
# DNS 확인
nslookup chwlabs.dev

# 포트 확인
sudo netstat -tlnp | grep -E '80|443'

# 방화벽 확인 (AWS Security Group)
# 인바운드 규칙: 80, 443 포트 개방
```

## 📝 체크리스트

### 로컬 개발 배포 전
- [ ] `nginx.conf.dev` 파일 존재
- [ ] `Dockerfile`이 `nginx.conf.dev` 복사
- [ ] SSL 설정 없음 확인
- [ ] `server_name localhost`

### EC2 프로덕션 배포 전
- [ ] `nginx.conf.prod` 파일 존재
- [ ] `Dockerfile.prod`가 `nginx.conf.prod` 복사
- [ ] Let's Encrypt 인증서 발급 완료
- [ ] 인증서 경로 확인 (`/etc/letsencrypt/live/`)
- [ ] DNS A 레코드 설정 완료
- [ ] AWS Security Group 80, 443 포트 개방

## 💡 팁

### 로컬에서 HTTPS 테스트하려면

```bash
# self-signed 인증서 생성
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/localhost.key -out nginx/localhost.crt

# nginx.conf.dev에 SSL 설정 추가
# (하지만 개발에는 HTTP만 사용하는 것을 권장)
```

### 설정 파일 문법 확인

```bash
# 로컬
docker exec research-agent-nginx nginx -t

# 설정 다시 로드 (재시작 없이)
docker exec research-agent-nginx nginx -s reload
```

### 도메인 변경 시

`nginx.conf.prod`에서:
```nginx
server_name your-new-domain.com;
ssl_certificate /etc/letsencrypt/live/your-new-domain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/your-new-domain.com/privkey.pem;
```

## 🔗 참고 링크

- [Nginx 공식 문서](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/)
- [SSL Labs 테스트](https://www.ssllabs.com/ssltest/)
