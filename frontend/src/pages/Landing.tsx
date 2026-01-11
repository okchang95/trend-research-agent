import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { createUser } from '../utils/api';

export const Landing: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated, login } = useAuth();
  
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showSignupModal, setShowSignupModal] = useState(false);
  
  const [loginName, setLoginName] = useState('');
  const [signupName, setSignupName] = useState('');
  const [signupPassword, setSignupPassword] = useState('');

  // 이미 로그인된 상태면 채팅 페이지로 리다이렉트
  useEffect(() => {
    if (isAuthenticated) {
      navigate('/chat');
    }
  }, [isAuthenticated, navigate]);

  const handleLogin = async () => {
    const userName = loginName.trim();
    
    if (!userName) {
      alert('유저 이름을 입력해주세요.');
      return;
    }

    try {
      await login(userName);
      setShowLoginModal(false);
      setLoginName('');
      navigate('/chat');
    } catch (error) {
      alert('유저를 찾을 수 없습니다.');
    }
  };

  const handleSignup = async () => {
    const userName = signupName.trim();
    const password = signupPassword.trim();

    if (!userName) {
      alert('유저 이름을 입력해주세요.');
      return;
    }

    if (!password) {
      alert('비밀번호를 입력해주세요.');
      return;
    }

    try {
      await createUser(userName, password);
      setShowSignupModal(false);
      setSignupName('');
      setSignupPassword('');
      
      // 회원가입 성공 후 로그인 여부 확인
      if (window.confirm('회원가입이 완료되었습니다.\n로그인하시겠습니까?')) {
        try {
          await login(userName);
          navigate('/chat');
        } catch (error) {
          alert('자동 로그인에 실패했습니다. 다시 로그인해주세요.');
        }
      }
    } catch (error) {
      alert('회원가입 실패: ' + (error as Error).message);
    }
  };

  return (
    <div className="landing-page">
      <div className="landing-content">
        <h1 className="landing-title">🤖 AI 트렌드 분석 어시스턴트</h1>
        <p className="landing-description">
          연구/기술/산업 등의 <strong>최신 트렌드</strong>를 분석하여 종합 보고서를 제공하는 AI 어시스턴트입니다.
        </p>

        <div className="landing-features">
          <div className="landing-feature-item">
            <span className="landing-feature-icon">🔍</span>
            <div>
              <h3>요구사항 명확화</h3>
              <p>대화를 통해 분석하고 싶은 주제와 범위를 명확히 파악합니다.</p>
            </div>
          </div>
          <div className="landing-feature-item">
            <span className="landing-feature-icon">📚</span>
            <div>
              <h3>자료 수집</h3>
              <p>웹 검색과 학술 논문 검색(ArXiv)을 통해 <strong>최신 정보</strong>를 수집합니다.</p>
            </div>
          </div>
          <div className="landing-feature-item">
            <span className="landing-feature-icon">✍️</span>
            <div>
              <h3>보고서 작성</h3>
              <p>수집된 자료를 바탕으로 테이블, 다이어그램, 출처가 포함된 마크다운 보고서를 생성합니다.</p>
            </div>
          </div>
        </div>

        <div className="landing-actions">
          <button
            className="landing-btn landing-btn-primary"
            onClick={() => setShowLoginModal(true)}
          >
            로그인
          </button>
          <button
            className="landing-btn landing-btn-secondary"
            onClick={() => setShowSignupModal(true)}
          >
            회원가입
          </button>
        </div>
      </div>

      {/* 로그인 모달 */}
      {showLoginModal && (
        <div className="modal" style={{ display: 'flex' }}>
          <div className="modal-content">
            <h2>로그인</h2>
            <input
              type="text"
              placeholder="demo: test"
              autoComplete="off"
              value={loginName}
              onChange={(e) => setLoginName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
            />
            <div className="modal-actions">
              <button className="modal-btn" onClick={handleLogin}>
                로그인
              </button>
              <button
                className="modal-btn modal-btn-secondary"
                onClick={() => {
                  setShowLoginModal(false);
                  setLoginName('');
                }}
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 회원가입 모달 */}
      {showSignupModal && (
        <div className="modal" style={{ display: 'flex' }}>
          <div className="modal-content">
            <h2>회원가입</h2>
            <input
              type="text"
              placeholder="유저 이름을 입력하세요"
              autoComplete="off"
              value={signupName}
              onChange={(e) => setSignupName(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  document.getElementById('signupPasswordInput')?.focus();
                }
              }}
            />
            <input
              id="signupPasswordInput"
              type="password"
              placeholder="비밀번호를 입력하세요"
              autoComplete="off"
              value={signupPassword}
              onChange={(e) => setSignupPassword(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSignup()}
            />
            <div className="modal-actions">
              <button className="modal-btn" onClick={handleSignup}>
                회원가입
              </button>
              <button
                className="modal-btn modal-btn-secondary"
                onClick={() => {
                  setShowSignupModal(false);
                  setSignupName('');
                  setSignupPassword('');
                }}
              >
                취소
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
