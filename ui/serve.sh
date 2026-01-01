#!/bin/bash

# UI 서버 실행 스크립트
# Python의 내장 HTTP 서버를 사용하여 ui 폴더를 서빙합니다.

PORT=${1:-3000}

echo "UI 서버를 시작합니다..."
echo "브라우저에서 http://localhost:$PORT 를 열어주세요."
echo "종료하려면 Ctrl+C를 누르세요."
echo ""

cd "$(dirname "$0")"
python3 -m http.server $PORT

