import { API_USERS_URL, API_THREADS_URL } from './env';
import { User, Thread, Message } from '../types';

interface ApiResponse<T> {
  success: boolean;
  data?: T;
  message?: string;
}

/**
 * 사용자 조회
 */
export const getUser = async (name: string): Promise<User | null> => {
  try {
    const response = await fetch(`${API_USERS_URL}?name=${encodeURIComponent(name)}`);
    const result: ApiResponse<User> = await response.json();
    
    if (result.success && result.data) {
      return result.data;
    }
    return null;
  } catch (error) {
    console.error('Error getting user:', error);
    throw error;
  }
};

/**
 * 사용자 등록
 */
export const createUser = async (name: string, password: string): Promise<User | null> => {
  try {
    const response = await fetch(API_USERS_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, password }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result: ApiResponse<User> = await response.json();
    
    if (result.success && result.data) {
      return result.data;
    }
    return null;
  } catch (error) {
    console.error('Error creating user:', error);
    throw error;
  }
};

/**
 * Thread 리스트 조회
 */
export const getThreads = async (userId: string): Promise<Thread[]> => {
  try {
    const response = await fetch(`${API_THREADS_URL}?user_id=${encodeURIComponent(userId)}`);
    const result: ApiResponse<Thread[]> = await response.json();
    
    if (result.success && result.data) {
      return result.data;
    }
    return [];
  } catch (error) {
    console.error('Error getting threads:', error);
    throw error;
  }
};

/**
 * Thread 생성
 */
export const createThread = async (userId: string): Promise<Thread | null> => {
  try {
    const response = await fetch(API_THREADS_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userId }),
    });
    
    const result: ApiResponse<Thread> = await response.json();
    
    if (result.success && result.data) {
      return result.data;
    }
    return null;
  } catch (error) {
    console.error('Error creating thread:', error);
    throw error;
  }
};

/**
 * Thread 메시지 조회
 */
export const getThreadMessages = async (threadId: string): Promise<Message[]> => {
  try {
    const response = await fetch(`${API_THREADS_URL}/${threadId}/messages`);
    const result: ApiResponse<Message[]> = await response.json();
    
    if (result.success && result.data) {
      return result.data;
    }
    return [];
  } catch (error) {
    console.error('Error getting messages:', error);
    throw error;
  }
};
