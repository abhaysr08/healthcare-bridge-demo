import { forwardRef } from 'react';
import ChatBubble from './ChatBubble';
import TypingIndicator from './TypingIndicator';

const ChatMessageList = forwardRef(function ChatMessageList(
  { messages, isLoading },
  ref
) {
  return (
    <div className="px-4 py-6 space-y-4 max-w-3xl mx-auto w-full">
      {messages.map((msg, idx) => (
        <ChatBubble key={idx} message={msg} />
      ))}
      {isLoading && <TypingIndicator />}
      <div ref={ref} />
    </div>
  );
});

export default ChatMessageList;
