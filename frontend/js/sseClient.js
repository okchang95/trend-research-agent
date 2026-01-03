/**
 * SSE 클라이언트 모듈
 * SSE 연결 및 파싱 담당
 */

/**
 * SSE 스트림 파싱 및 이벤트 처리
 */
class SSEClient {
    constructor(apiUrl) {
        this.apiUrl = apiUrl;
    }

    /**
     * SSE 스트림 연결 및 이벤트 처리
     */
    async stream(requestBody, onEvent) {
        const response = await fetch(this.apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const reader = response.body.getReader();
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
                buffer = lines.pop(); // 마지막 불완전한 라인은 버퍼에 보관
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = line.slice(6); // 'data: ' 제거
                        try {
                            const event = JSON.parse(data);
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
                    const event = JSON.parse(data);
                    onEvent(event);
                } catch (e) {
                    console.error('Failed to parse SSE buffer:', e);
                }
            }
        } finally {
            reader.releaseLock();
        }
    }
}

