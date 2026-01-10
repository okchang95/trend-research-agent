import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getUser } from '../utils/api';

interface AuthContextType {
  userId: string | null;
  userName: string | null;
  isAuthenticated: boolean;
  login: (userName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // 페이지 로드 시 localStorage에서 로그인 상태 확인
  useEffect(() => {
    const storedUserName = localStorage.getItem('userId'); // 키는 'userId'지만 값은 user_name
    if (storedUserName) {
      // user_name으로 user_id 조회
      getUser(storedUserName)
        .then((user) => {
          if (user) {
            setUserId(user.user_id);
            setUserName(storedUserName);
            setIsAuthenticated(true);
          } else {
            // 유저를 찾을 수 없으면 로그아웃 처리
            localStorage.removeItem('userId');
          }
        })
        .catch((error) => {
          console.error('Error loading user:', error);
          localStorage.removeItem('userId');
        });
    }
  }, []);

  const login = async (name: string) => {
    try {
      const user = await getUser(name);
      if (user) {
        setUserId(user.user_id);
        setUserName(name);
        setIsAuthenticated(true);
        localStorage.setItem('userId', name);
      } else {
        throw new Error('User not found');
      }
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = () => {
    setUserId(null);
    setUserName(null);
    setIsAuthenticated(false);
    localStorage.removeItem('userId');
  };

  return (
    <AuthContext.Provider value={{ userId, userName, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
