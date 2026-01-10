import React, { useState, FormEvent, KeyboardEvent } from 'react';

interface InputSectionProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export const InputSection: React.FC<InputSectionProps> = ({ onSend, disabled = false }) => {
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
    if (e.key === 'Enter' && !disabled) {
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
          disabled={disabled}
        />
        <button
          className="search-btn"
          onClick={() => handleSubmit()}
          disabled={disabled}
        >
          {disabled ? '검색 중...' : '전송'}
        </button>
      </div>
    </div>
  );
};
