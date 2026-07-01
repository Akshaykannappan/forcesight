import { useState, useRef, useEffect } from 'react';

export default function ChatInput({ onSend, onStop, isLoading }) {
  const [input, setInput] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (!isLoading && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isLoading]);

  const handleSubmit = (e) => {
    e.preventDefault();
    const query = input.trim();
    if (!query || isLoading) return;
    
    setInput('');
    onSend(query);
  };

  return (
    <footer className="chat-input-area">
      <form className="chat-form" onSubmit={handleSubmit}>
        <input
          ref={inputRef}
          type="text"
          className="chat-input"
          placeholder="Ask a question about your data..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
          autoComplete="off"
          required
        />
        
        {isLoading ? (
          <button type="button" className="btn btn-danger" onClick={onStop}>
            Stop
          </button>
        ) : (
          <button type="submit" className="btn btn-primary" disabled={!input.trim()}>
            Send
          </button>
        )}
      </form>
    </footer>
  );
}
