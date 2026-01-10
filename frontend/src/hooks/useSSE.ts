import { useState, useCallback, useRef } from 'react';
import { API_STREAM_URL } from '../utils/env';
import { SSEEvent } from '../types';

interface UseSSEReturn {
  isStreaming: boolean;
  error: string | null;
  stream: (requestBody: any, onEvent: (event: SSEEvent) => void) => Promise<void>;
  cancelStream: () => void;
}

export const useSSE = (): UseSSEReturn => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);
    }
  }, []);

  const stream = useCallback(async (requestBody: any, onEvent: (event: SSEEvent) => void) => {
    // 기존 스트림이 있으면 취소
    cancelStream();

    setIsStreaming(true);
    setError(null);

    // 새로운 AbortController 생성
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const response = await fetch(API_STREAM_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('Response body is null');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();

          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || ''; // 마지막 불완전한 라인은 버퍼에 보관

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6); // 'data: ' 제거
              try {
                const event: SSEEvent = JSON.parse(data);
                onEvent(event);
              } catch (e) {
                console.error('Failed to parse SSE data:', e);
              }
            }
          }
        }

        // 버퍼에 남은 데이터 처리
        if (buffer.startsWith('data: ')) {
          const data = buffer.slice(6);
          try {
            const event: SSEEvent = JSON.parse(data);
            onEvent(event);
          } catch (e) {
            console.error('Failed to parse SSE buffer:', e);
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        console.log('Stream cancelled');
      } else {
        console.error('Stream error:', err);
        setError(err.message || 'Unknown error occurred');
        throw err;
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, [cancelStream]);

  return {
    isStreaming,
    error,
    stream,
    cancelStream,
  };
};
