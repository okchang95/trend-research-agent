# 배포 가이드

## 배포 방법

### 방법 1: Docker 사용 (추천)
Docker를 사용하면 환경 설정이 간단하고 일관성 있게 배포할 수 있습니다.

### 방법 2: 직접 배포 (Conda 환경)
EC2에 직접 conda 환경을 설정하여 배포합니다.

---

## 방법 1: Docker 배포 (Route53 + Elastic IP)

과제용이므로 가장 간단한 방법으로 배포합니다.

### 1. EC2 인스턴스 준비

1. EC2 인스턴스 생성 (Ubuntu 22.04 LTS 권장)
2. Elastic IP 할당 및 연결
3. 보안 그룹 설정:
   - 인바운드 규칙: HTTP (80), HTTPS (443), SSH (22)

### 2. Route53 설정

1. Route53에서 호스팅 영역 생성 또는 기존 영역 사용
2. A 레코드 생성:
   - 이름: `@` (루트 도메인) 또는 `research` (서브도메인)
   - 값: Elastic IP 주소
   - TTL: 300

예: `research.chwlabs.dev` 또는 `chwlabs.dev`

### 3. EC2 인스턴스 설정

#### 3.1 Docker 설치

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y docker.io docker-compose git nginx curl

# Docker 서비스 시작 및 자동 시작 설정
sudo systemctl start docker
sudo systemctl enable docker

# ubuntu 사용자를 docker 그룹에 추가 (sudo 없이 docker 사용)
sudo usermod -aG docker ubuntu
newgrp docker  # 또는 재로그인
```

#### 3.2 프로젝트 클론

```bash
cd /home/ubuntu
git clone <your-github-repo-url>
cd <project-directory>
```

#### 3.3 환경 변수 설정

```bash
nano .env
```

`.env` 파일 내용:
```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

#### 3.4 Docker 이미지 빌드

```bash
docker build -t research-agent .
```

#### 3.5 Docker 컨테이너 실행

```bash
docker run -d \
  --name research-agent \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  research-agent
```

또는 systemd 서비스로 관리하려면:

#### 3.6 systemd 서비스 생성 (선택사항)

```bash
sudo nano /etc/systemd/system/research-agent.service
```

서비스 파일 내용:
```ini
[Unit]
Description=Research Agent Docker Container
After=docker.service
Requires=docker.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/<project-directory>
ExecStart=/usr/bin/docker start -a research-agent
ExecStop=/usr/bin/docker stop research-agent
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

서비스 활성화 및 시작:
```bash
sudo systemctl daemon-reload
sudo systemctl enable research-agent
sudo systemctl start research-agent
sudo systemctl status research-agent
```

**참고**: Docker 컨테이너를 직접 관리하는 것이 더 간단할 수 있습니다.

### 4. nginx 설정 (포트 80 → 8000 프록시)

#### 4.1 nginx 설정 파일 생성

```bash
sudo nano /etc/nginx/sites-available/research-agent
```

설정 파일 내용:
```nginx
server {
    listen 80;
    server_name chwlabs.dev www.chwlabs.dev;  # 또는 research.chwlabs.dev

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # SSE를 위한 설정
        proxy_buffering off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

#### 4.2 nginx 활성화 및 시작

```bash
sudo ln -s /etc/nginx/sites-available/research-agent /etc/nginx/sites-enabled/
sudo nginx -t  # 설정 테스트
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### 5. 방화벽 설정 (UFW)

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 6. SSL 인증서 설정 (선택사항, HTTPS 사용 시)

Let's Encrypt 사용:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d chwlabs.dev -d www.chwlabs.dev
```

### 7. 배포 확인

1. 브라우저에서 `http://chwlabs.dev` 접속
2. API 테스트: `http://chwlabs.dev/health`
3. 프론트엔드 확인: `http://chwlabs.dev/`

## 대안: nginx 없이 직접 80 포트 사용 (더 간단)

nginx를 사용하지 않고 싶다면:

1. Docker 컨테이너 실행 시 포트를 80으로 변경:
```bash
docker run -d \
  --name research-agent \
  --restart unless-stopped \
  -p 80:8000 \
  --env-file .env \
  research-agent
```

또는 Dockerfile을 수정하여 포트 80을 직접 사용:
```dockerfile
EXPOSE 80
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
```

**주의**: 포트 80을 사용하려면 Docker를 root 권한으로 실행하거나 `setcap` 설정이 필요할 수 있습니다.

---

## 방법 2: 직접 배포 (Conda 환경)

Docker를 사용하지 않고 직접 conda 환경으로 배포하는 방법입니다.

### 1-2. EC2 및 Route53 설정
위의 "방법 1"과 동일합니다.

### 3. EC2 인스턴스 설정

#### 3.1 시스템 업데이트 및 필수 패키지 설치

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git nginx curl
```

#### 3.2 Miniconda/Anaconda 설치 (없는 경우)

```bash
# Miniconda 설치
cd /tmp
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
echo 'export PATH="$HOME/miniconda3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

#### 3.3 프로젝트 클론

```bash
cd /home/ubuntu
git clone <your-github-repo-url>
cd <project-directory>
```

#### 3.4 Conda 가상 환경 설정

```bash
# conda 환경 생성
conda create -n research-agent python=3.13 -y
conda activate research-agent

# 의존성 설치
pip install -r requirements.txt
```

#### 3.5 환경 변수 설정

```bash
nano .env
```

`.env` 파일 내용:
```env
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

#### 3.6 systemd 서비스 생성

```bash
sudo nano /etc/systemd/system/research-agent.service
```

서비스 파일 내용:
```ini
[Unit]
Description=Research Agent FastAPI Application
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/<project-directory>
Environment="PATH=/home/ubuntu/miniconda3/envs/research-agent/bin:/home/ubuntu/miniconda3/bin:$PATH"
ExecStart=/home/ubuntu/miniconda3/envs/research-agent/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**참고**: conda 환경 경로가 다를 수 있습니다. 다음 명령어로 확인하세요:
```bash
conda activate research-agent
which uvicorn  # 이 경로를 ExecStart에 사용
```

서비스 활성화 및 시작:
```bash
sudo systemctl daemon-reload
sudo systemctl enable research-agent
sudo systemctl start research-agent
sudo systemctl status research-agent
```

### 4. nginx 설정
위의 "방법 1"과 동일합니다.

## 로그 확인

### Docker 사용 시

```bash
# Docker 컨테이너 로그
docker logs -f research-agent

# nginx 로그
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 직접 배포 시

```bash
# FastAPI 애플리케이션 로그
sudo journalctl -u research-agent -f

# nginx 로그
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 업데이트 배포

### Docker 사용 시

```bash
cd /home/ubuntu/<project-directory>
git pull
docker build -t research-agent .
docker stop research-agent
docker rm research-agent
docker run -d \
  --name research-agent \
  --restart unless-stopped \
  -p 8000:8000 \
  --env-file .env \
  research-agent
```

### 직접 배포 시

```bash
cd /home/ubuntu/<project-directory>
git pull
conda activate research-agent
pip install -r requirements.txt
sudo systemctl restart research-agent
```

## 문제 해결

### 서비스가 시작되지 않는 경우
```bash
sudo systemctl status research-agent
sudo journalctl -u research-agent -n 50
```

### 포트가 이미 사용 중인 경우
```bash
sudo lsof -i :8000
sudo netstat -tulpn | grep 8000
```

### nginx 설정 오류
```bash
sudo nginx -t
sudo systemctl status nginx
```

