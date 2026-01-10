import React, { useState, FormEvent, KeyboardEvent } from 'react';

interface InputSectionProps {
  onSend: (message: string) => void;
  onStop?: () => void;
  disabled?: boolean;
  isStreaming?: boolean;
}

export const InputSection: React.FC<InputSectionProps> = ({ 
  onSend, 
  onStop,
  disabled = false,
  isStreaming = false
}) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e?: FormEvent) => {
    e?.preventDefault();
    
    const message = input.trim();
    if (!message) {
      alert('메시지를 입력해주세요.');
      return;
    }

    onSend(message);
    setInput('');
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !disabled && !isStreaming) {
      handleSubmit();
    }
  };

  return (
    <div className="input-section">
      <div className="input-wrapper">
        <input
          type="text"
          id="userInput"
          placeholder="분석하고 싶은 주제를 입력하세요..."
          autoComplete="off"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={isStreaming}
        />
        
        {isStreaming ? (
          <button
            className="stop-btn"
            onClick={onStop}
            title="응답 중지"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
              <rect x="5" y="5" width="10" height="10" rx="1"/>
            </svg>
          </button>
        ) : (
          <button
            className="search-btn"
            onClick={() => handleSubmit()}
            disabled={disabled}
          >
            전송
          </button>
        )}
      </div>
    </div>
  );
};
