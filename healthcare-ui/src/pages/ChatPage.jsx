import AppHeader from '../components/layout/AppHeader';
import ChatEmptyState from '../components/chat/ChatEmptyState';
import ChatMessageList from '../components/chat/ChatMessageList';
import ChatInput from '../components/chat/ChatInput';
import useChat from '../hooks/useChat';

export default function ChatPage() {
  const {
    messages,
    input,
    setInput,
    isLoading,
    sendMessage,
    messagesEndRef,
    textareaRef,
  } = useChat();

  const isEmpty = messages.length === 0;
  const firstName = 'Elisa'; // Hardcoded default user

  return (
    <div className="h-screen flex flex-col bg-navy">
      <AppHeader />
      {/* White rounded card - messages + input inside */}
      <div className="flex-1 mt-1 mb-3 mx-3 bg-white rounded-[2rem] overflow-hidden flex flex-col">
        <div className="flex-1 overflow-y-auto">
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
  );
}
