import { useState, useRef } from 'react';
import ChatContainer from './components/Chat/ChatContainer';
import MessageList from './components/Chat/MessageList';
import ChatInput from './components/Chat/ChatInput';

const API_URL = 'http://localhost:8000/chat';

export default function App() {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef(null);

  const handleSend = async (query) => {
    // Add user message
    setMessages(prev => [...prev, { type: 'user', text: query }]);
    setIsLoading(true);

    // show the typing indicator immediately while waiting for the response
    setMessages(prev => [...prev, { type: 'typing' }]);

    abortControllerRef.current = new AbortController();

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();

      // replace typing indicator with the actual response
      if (data.clarification_needed) {
        setMessages(prev => [...prev.filter(m => m.type !== 'typing'), {
          type: 'ai',
          text: '',
          sql: '',
          clarificationNeeded: true,
          clarifyingQuestions: data.clarifying_questions || [],
        }]);
      } else {
        const summary = data.summary || 'No summary provided.';
        const sql = data.sql || '';
        setMessages(prev => [...prev.filter(m => m.type !== 'typing'), { type: 'ai', text: summary, sql }]);
      }

    } catch (error) {
      setMessages(prev => prev.filter(m => m.type !== 'typing'));
      if (error.name === 'AbortError') {
        setMessages(prev => [...prev, { type: 'system', text: 'Request cancelled' }]);
      } else {
        console.error('Fetch error:', error);
        setMessages(prev => [...prev, { type: 'system', text: 'Something went wrong, try again' }]);
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  return (
    <ChatContainer>
      <MessageList messages={messages} onSuggestionClick={handleSend} />
      <ChatInput 
        onSend={handleSend} 
        onStop={handleStop} 
        isLoading={isLoading} 
      />
    </ChatContainer>
  );
}
