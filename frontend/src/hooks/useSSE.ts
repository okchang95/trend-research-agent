import { useState, useCallback, useRef } from 'react';
import { API_STREAM_URL } from '../utils/env';
import { SSEEvent } from '../types';

interface StreamState {
  abortController: AbortController;
}

interface UseSSEReturn {
  streamingThreads: Set<string>;
  isThreadStreaming: (threadId: string | null) => boolean;
  error: string | null;
  stream: (threadId: string, requestBody: any, onEvent: (event: SSEEvent) => void) => Promise<void>;
  cancelStream: (threadId: string) => void;
  cancelAllStreams: () => void;
}

export const useSSE = (): UseSSEReturn => {
  const [streamingThreads, setStreamingThreads] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const streamStatesRef = useRef<Map<string, StreamState>>(new Map());

  const isThreadStreaming = useCallback((threadId: string | null) => {
    if (!threadId) return false;
    return streamingThreads.has(threadId);
  }, [streamingThreads]);

  const cancelStream = useCallback((threadId: string) => {
    const state = streamStatesRef.current.get(threadId);
    if (state) {
      state.abortController.abort();
      streamStatesRef.current.delete(threadId);
      
      setStreamingThreads(prev => {
        const newSet = new Set(prev);
        newSet.delete(threadId);
        return newSet;
      });
    }
  }, []);

  const cancelAllStreams = useCallback(() => {
    streamStatesRef.current.forEach((state) => {
      state.abortController.abort();
    });
    streamStatesRef.current.clear();
    setStreamingThreads(new Set());
  }, []);

  const stream = useCallback(async (
    threadId: string,
    requestBody: any, 
    onEvent: (event: SSEEvent) => void
  ) => {
    // 해당 thread의 기존 스트림이 있으면 취소
    if (streamStatesRef.current.has(threadId)) {
      cancelStream(threadId);
    }

    const abortController = new AbortController();
    streamStatesRef.current.set(threadId, { abortController });

    setStreamingThreads(prev => new Set(prev).add(threadId));
    setError(null);

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
        console.log(`Stream cancelled for thread ${threadId}`);
      } else {
        console.error('Stream error:', err);
        setError(err.message || 'Unknown error occurred');
        throw err;
      }
    } finally {
      streamStatesRef.current.delete(threadId);
      setStreamingThreads(prev => {
        const newSet = new Set(prev);
        newSet.delete(threadId);
        return newSet;
      });
    }
  }, [cancelStream]);

  return {
    streamingThreads,
    isThreadStreaming,
    error,
    stream,
    cancelStream,
    cancelAllStreams,
  };
};
