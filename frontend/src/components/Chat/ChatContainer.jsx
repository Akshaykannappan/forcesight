export default function ChatContainer({ children }) {
  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="chat-header-logo">FS</div>
        <h1>ForceSight Data Assistant</h1>
      </header>
      {children}
    </div>
  );
}
