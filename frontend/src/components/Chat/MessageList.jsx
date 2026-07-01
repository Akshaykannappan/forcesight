import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

export default function MessageList({ messages, onSuggestionClick }) {
  const listRef = useRef(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <main className="message-list" ref={listRef}>
      {messages.length === 0 && (
        <div className="message-wrapper system">
          <div className="message-bubble" style={{ background: 'transparent', border: 'none', color: '#64748b', boxShadow: 'none' }}>
            Hello! Ask a question about your data to get started.
          </div>
        </div>
      )}
      {messages.map((msg, index) => (
        <MessageBubble key={index} message={msg} onSuggestionClick={onSuggestionClick} />
      ))}
    </main>
  );
}
