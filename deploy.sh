#!/bin/bash

# 배포 스크립트
# 사용법: ./deploy.sh [dev|prod]

set -e

MODE=${1:-dev}

echo "🚀 배포 모드: $MODE"

if [ "$MODE" = "dev" ]; then
    echo "📦 개발 모드 배포 시작..."
    
    # React 빌드
    echo "🔨 React 빌드 중..."
    cd frontend
    npm install
    npm run build
    cd ..
    
    # Docker Compose 실행
    echo "🐳 Docker Compose 실행 중..."
    docker compose -f docker-compose.dev.yml up --build -d
    
    echo "✅ 개발 모드 배포 완료!"
    echo "🌐 접속: http://localhost"
    
elif [ "$MODE" = "prod" ]; then
    echo "📦 프로덕션 모드 배포 시작..."
    
    # Docker Compose 실행 (React 빌드 포함)
    echo "🐳 Docker Compose 실행 중 (React 빌드 포함)..."
    docker compose -f docker-compose.prod.yml up --build -d
    
    echo "✅ 프로덕션 모드 배포 완료!"
    echo "🌐 접속: http://localhost"
    
else
    echo "❌ 잘못된 모드입니다. dev 또는 prod를 선택하세요."
    echo "사용법: ./deploy.sh [dev|prod]"
    exit 1
fi

echo ""
echo "📊 컨테이너 상태:"
if [ "$MODE" = "dev" ]; then
    docker compose -f docker-compose.dev.yml ps
else
    docker compose -f docker-compose.prod.yml ps
fi

echo ""
if [ "$MODE" = "dev" ]; then
    echo "📝 로그 확인: docker-compose -f docker-compose.dev.yml logs -f"
    echo "🛑 중지: docker-compose -f docker-compose.dev.yml down"
else
    echo "📝 로그 확인: docker-compose -f docker-compose.prod.yml logs -f"
    echo "🛑 중지: docker-compose -f docker-compose.prod.yml down"
fi
