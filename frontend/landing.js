/**
 * 렌딩 페이지 스크립트
 * 로그인 및 회원가입 처리
 */

// API 엔드포인트 설정
// .env 파일에서 환경 변수 읽기 (window.__ENV__에 설정됨)
// 프로덕션 환경에서는 항상 같은 origin 사용 (nginx 프록시를 통해)
const isLocalDev = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocalDev 
    ? (window.__ENV__?.API_BASE_URL || 'http://localhost:8000')
    : window.location.origin; // 프로덕션: 같은 origin 사용 (nginx 프록시)
const API_USERS_URL = API_BASE_URL + '/api/users';

// DOM 요소
const landingPage = document.getElementById('landingPage');
const loginModal = document.getElementById('loginModal');
const signupModal = document.getElementById('signupModal');
const loginBtn = document.getElementById('loginBtn');
const signupBtn = document.getElementById('signupBtn');
const loginNameInput = document.getElementById('loginNameInput');
const loginSubmit = document.getElementById('loginSubmit');
const loginCancel = document.getElementById('loginCancel');
const signupNameInput = document.getElementById('signupNameInput');
const signupPasswordInput = document.getElementById('signupPasswordInput');
const signupSubmit = document.getElementById('signupSubmit');
const signupCancel = document.getElementById('signupCancel');

// 페이지 로드 시 초기화
window.addEventListener('DOMContentLoaded', () => {
    // 로그인/회원가입 버튼 이벤트
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            if (loginModal) loginModal.style.display = 'flex';
        });
    }
    if (signupBtn) {
        signupBtn.addEventListener('click', () => {
            if (signupModal) signupModal.style.display = 'flex';
        });
    }
    
    // 로그인 모달 이벤트
    if (loginSubmit) {
        loginSubmit.addEventListener('click', handleLogin);
    }
    if (loginCancel) {
        loginCancel.addEventListener('click', () => {
            if (loginModal) loginModal.style.display = 'none';
            if (loginNameInput) loginNameInput.value = '';
        });
    }
    if (loginNameInput) {
        loginNameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleLogin();
            }
        });
    }
    
    // 회원가입 모달 이벤트
    if (signupSubmit) {
        signupSubmit.addEventListener('click', handleSignup);
    }
    if (signupCancel) {
        signupCancel.addEventListener('click', () => {
            if (signupModal) signupModal.style.display = 'none';
            if (signupNameInput) signupNameInput.value = '';
            if (signupPasswordInput) signupPasswordInput.value = '';
        });
    }
    if (signupNameInput) {
        signupNameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && signupPasswordInput) {
                signupPasswordInput.focus();
            }
        });
    }
    if (signupPasswordInput) {
        signupPasswordInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleSignup();
            }
        });
    }
    
    // 기존 로그인 상태 확인
    const userId = localStorage.getItem('userId');
    if (userId) {
        // 이미 로그인된 상태면 메인 페이지로 리다이렉트
        window.location.href = '/index.html';
    }
});

/**
 * 로그인 처리
 */
async function handleLogin() {
    if (!loginNameInput) {
        console.error('loginNameInput element not found');
        return;
    }
    
    const userName = loginNameInput.value.trim();
    
    if (!userName) {
        alert('유저 이름을 입력해주세요.');
        return;
    }
    
    try {
        // 유저 조회
        const response = await fetch(`${API_USERS_URL}?name=${encodeURIComponent(userName)}`);
        const result = await response.json();
        
        if (result.success && result.data) {
            // 로그인 성공
            localStorage.setItem('userId', userName);
            if (loginModal) loginModal.style.display = 'none';
            if (loginNameInput) loginNameInput.value = '';
            
            // 메인 페이지로 리다이렉트
            window.location.href = '/index.html';
        } else {
            alert('유저를 찾을 수 없습니다: ' + (result.message || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('Error during login:', error);
        alert('로그인 중 오류가 발생했습니다.');
    }
}

/**
 * 회원가입 처리
 */
async function handleSignup() {
    if (!signupNameInput || !signupPasswordInput) {
        console.error('Signup input elements not found');
        return;
    }
    
    const userName = signupNameInput.value.trim();
    const password = signupPasswordInput.value.trim();
    
    if (!userName) {
        alert('유저 이름을 입력해주세요.');
        return;
    }
    
    if (!password) {
        alert('비밀번호를 입력해주세요.');
        return;
    }
    
    try {
        // 유저 등록
        const response = await fetch(API_USERS_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ name: userName, password: password })
        });
        
        // HTTP 상태 코드 확인
        if (!response.ok) {
            console.error('HTTP Error:', response.status, response.statusText);
            const errorText = await response.text();
            console.error('Error response:', errorText);
            alert(`회원가입 실패: ${response.status} ${response.statusText}`);
            return;
        }
        
        const result = await response.json();
        
        if (result.success) {
            // 회원가입 성공
            alert('등록되었습니다.');
            if (signupModal) signupModal.style.display = 'none';
            if (signupNameInput) signupNameInput.value = '';
            if (signupPasswordInput) signupPasswordInput.value = '';
        } else {
            alert('회원가입 실패: ' + (result.message || '알 수 없는 오류'));
        }
    } catch (error) {
        console.error('Error during signup:', error);
        alert('회원가입 중 오류가 발생했습니다: ' + error.message);
    }
}
