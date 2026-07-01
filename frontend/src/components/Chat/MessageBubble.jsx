import { useState } from 'react';

export default function MessageBubble({ message, onSuggestionClick }) {
  const [showSql, setShowSql] = useState(false);
  const { type, text, sql, clarificationNeeded, clarifyingQuestions } = message;

  if (type === 'typing') {
    return (
      <div className="message-wrapper ai">
        <span className="message-label">Assistant</span>
        <div className="message-bubble typing-bubble">
          <span className="typing-dot" />
          <span className="typing-dot" />
          <span className="typing-dot" />
        </div>
      </div>
    );
  }

  return (
    <div className={`message-wrapper ${type}`}>
      {type === 'user' && <span className="message-label user-label">You</span>}
      {type === 'ai' && <span className="message-label">Assistant</span>}
      <div className="message-bubble">
        {type === 'ai' ? (
          <>
            {clarificationNeeded && clarifyingQuestions?.length > 0 ? (
              <div className="clarification-container">
                <p className="clarification-prompt">
                  Sorry, I couldn't find what you were looking for. Try asking:
                </p>
                <div className="clarification-questions">
                  {clarifyingQuestions.map((q, i) => (
                    <button
                      key={i}
                      className="suggestion-chip"
                      type="button"
                      onClick={() => onSuggestionClick(q)}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <>
                <div className="message-summary">{text}</div>
                {sql && (
                  <div className="sql-container">
                    <button
                      className="sql-toggle-btn"
                      onClick={() => setShowSql(!showSql)}
                      type="button"
                    >
                      <span className={`sql-toggle-icon ${showSql ? 'open' : ''}`}>▶</span>
                      {showSql ? 'Hide SQL' : 'View SQL'}
                    </button>
                    {showSql && (
                      <div className="sql-content">
                        <pre>
                          <code>{sql}</code>
                        </pre>
                      </div>
                    )}
                  </div>
                )}
              </>
            )}
          </>
        ) : (
          <div className="message-text">{text}</div>
        )}
      </div>
    </div>
  );
}
