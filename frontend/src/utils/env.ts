/**
 * 환경 변수 관리 유틸리티
 * .env 파일에서 VITE_API_BASE_URL을 읽어옴
 * 없으면 window.location.origin 사용 (프로덕션 환경에서 nginx 프록시)
 */

export const getApiBaseUrl = (): string => {
  // .env에서 VITE_API_BASE_URL 읽기
  const envBaseUrl = import.meta.env.VITE_API_BASE_URL;
  
  // .env에 값이 있으면 그것을 사용, 없으면 window.location.origin 사용
  return envBaseUrl || window.location.origin;
};

export const API_BASE_URL = getApiBaseUrl();
export const API_STREAM_URL = `${API_BASE_URL}/api/chat/stream`;
export const API_THREADS_URL = `${API_BASE_URL}/api/threads`;
export const API_USERS_URL = `${API_BASE_URL}/api/users`;
