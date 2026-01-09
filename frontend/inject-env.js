#!/usr/bin/env node

/**
 * .env 파일을 읽어서 HTML 파일에 환경 변수를 주입하는 스크립트
 * 사용법: node inject-env.js
 */

const fs = require('fs');
const path = require('path');

// .env 파일 경로
const envPath = path.join(__dirname, '.env');
const indexHtmlPath = path.join(__dirname, 'index.html');
const landingHtmlPath = path.join(__dirname, 'landing.html');

// .env 파일 읽기
let envVars = {};
if (fs.existsSync(envPath)) {
    const envContent = fs.readFileSync(envPath, 'utf-8');
    envContent.split('\n').forEach(line => {
        line = line.trim();
        if (line && !line.startsWith('#')) {
            const [key, ...valueParts] = line.split('=');
            if (key && valueParts.length > 0) {
                envVars[key.trim()] = valueParts.join('=').trim();
            }
        }
    });
}

// API_BASE_URL 설정 (기본값: http://localhost:8000)
// .env 파일에서 API_BASE_URL 또는 VITE_API_BASE_URL 둘 다 지원
const API_BASE_URL = envVars.API_BASE_URL || envVars.VITE_API_BASE_URL || 'http://localhost:8000';

// 환경 변수를 JavaScript 객체로 변환
const envScript = `
    <script>
        // .env 파일에서 읽어온 환경 변수
        window.__ENV__ = {
            API_BASE_URL: '${API_BASE_URL}'
        };
    </script>
`;

// HTML 파일 업데이트 함수
function injectEnvToHtml(htmlPath) {
    if (!fs.existsSync(htmlPath)) {
        console.warn(`파일을 찾을 수 없습니다: ${htmlPath}`);
        return;
    }

    let htmlContent = fs.readFileSync(htmlPath, 'utf-8');
    
    // 기존 환경 변수 스크립트 제거
    htmlContent = htmlContent.replace(
        /<script>\s*\/\/\s*\.env.*?<\/script>/s,
        ''
    );
    
    // </head> 태그 앞에 환경 변수 스크립트 추가
    htmlContent = htmlContent.replace(
        '</head>',
        envScript + '\n</head>'
    );
    
    fs.writeFileSync(htmlPath, htmlContent, 'utf-8');
    console.log(`✓ ${path.basename(htmlPath)} 업데이트 완료`);
}

// HTML 파일들 업데이트
injectEnvToHtml(indexHtmlPath);
injectEnvToHtml(landingHtmlPath);

console.log('환경 변수 주입 완료!');
