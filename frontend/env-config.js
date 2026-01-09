/**
 * 환경 변수 설정 파일
 * .env 파일의 값을 여기서 설정하거나, 빌드 스크립트에서 자동으로 주입
 */

// .env 파일에서 읽어올 환경 변수
// 실제 사용 시에는 빌드 스크립트가 .env 파일을 읽어서 이 값을 업데이트합니다
const ENV_CONFIG = {
    API_BASE_URL: process.env.VITE_API_BASE_URL || 'http://localhost:8000'
};

// 브라우저에서 사용할 수 있도록 window 객체에 설정
if (typeof window !== 'undefined') {
    window.__ENV__ = ENV_CONFIG;
}

// Node.js 환경에서도 사용 가능하도록 export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ENV_CONFIG;
}
