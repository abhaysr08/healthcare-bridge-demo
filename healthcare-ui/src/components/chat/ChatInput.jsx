import { forwardRef, useCallback } from 'react';

const ChatInput = forwardRef(function ChatInput(
  { value, onChange, onSend, disabled },
  ref
) {
  const handleKeyDown = useCallback(
    (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        onSend();
      }
    },
    [onSend]
  );

  const adjustHeight = useCallback((e) => {
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  }, []);

  return (
    <div className="bg-white px-4 py-3 pb-4 shrink-0 border-t border-gray-100">
      <div className="flex items-end gap-2">
        <div className="flex-1 bg-gray-50 rounded-2xl px-4 py-2.5 flex items-end border border-gray-200 focus-within:ring-2 focus-within:ring-teal/30 focus-within:border-teal transition-shadow">
          <textarea
            ref={ref}
            value={value}
            onChange={(e) => {
              onChange(e.target.value);
              adjustHeight(e);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Digita la tua domanda"
            disabled={disabled}
            rows={1}
            className="flex-1 resize-none text-sm bg-transparent
                       focus:outline-none
                       disabled:cursor-not-allowed
                       max-h-[120px] overflow-y-auto placeholder-gray-400"
          />
        </div>
        <button
          onClick={onSend}
          disabled={disabled || !value.trim()}
          className="w-10 h-10 rounded-full bg-teal text-white flex items-center justify-center
                     shrink-0 hover:bg-teal-dark hover:shadow-lg active:scale-90 transition-all
                     disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="currentColor"
            stroke="none"
          >
            <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
          </svg>
        </button>
      </div>
    </div>
  );
});

export default ChatInput;
