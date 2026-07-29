import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import AppHeader from '../components/layout/AppHeader';
import ChatEmptyState from '../components/chat/ChatEmptyState';
import ChatMessageList from '../components/chat/ChatMessageList';
import ChatInput from '../components/chat/ChatInput';
import useChat from '../hooks/useChat';

export default function ChatPage() {
  const { user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const {
    messages,
    input,
    setInput,
    isLoading,
    sendMessage,
    messagesEndRef,
    textareaRef,
  } = useChat();

  useEffect(() => {
    if (location.state?.prefill) {
      setInput(location.state.prefill);
      navigate(location.pathname, { replace: true, state: {} });
    }
  }, [location.state, location.pathname, navigate, setInput]);

  const isEmpty = messages.length === 0;
  const firstName = user?.fullName?.split(' ')[0] || 'Utente';

  return (
    <div className="h-screen flex flex-col bg-chat-bg">
      <AppHeader />

      <div className="flex-1 min-h-0">
        <div className="max-w-3xl mx-auto px-4 py-5 h-full flex flex-col">
          <button
            onClick={() => navigate(-1)}
            className="text-sm text-navy/70 hover:text-navy mb-4 flex items-center gap-1 transition-colors shrink-0 self-start"
          >
            ← Back
          </button>

          <div className="flex-1 min-h-0 bg-white rounded-2xl border border-gray-100 shadow-card flex flex-col overflow-hidden animate-fade-in">
            <div className="flex-1 min-h-0 overflow-y-auto">
              {isEmpty ? (
                <ChatEmptyState userName={firstName} />
              ) : (
                <ChatMessageList
                  messages={messages}
                  isLoading={isLoading}
                  ref={messagesEndRef}
                />
              )}
            </div>
            <ChatInput
              value={input}
              onChange={setInput}
              onSend={() => sendMessage(input)}
              disabled={isLoading}
              ref={textareaRef}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
