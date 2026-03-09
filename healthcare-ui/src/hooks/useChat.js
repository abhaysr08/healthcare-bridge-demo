import { useState, useRef, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { api as chatApi } from '../services/authApi';

export default function useChat() {
  const { accessToken } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (!isLoading && textareaRef.current) {
      setTimeout(() => textareaRef.current?.focus(), 0);
    }
  }, [isLoading]);

  const sendMessage = useCallback(
    async (messageText) => {
      if (!messageText.trim() || isLoading) return;

      const userMessage = messageText.trim();
      setInput('');

      setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
      setIsLoading(true);

      try {
        const response = await chatApi.post(
          '/chat',
          {
            message: userMessage,
            conversation_history: messages.map(({ role, content, patientContext }) => ({
              role,
              content,
              patient_context: patientContext || null,
            })),
          },
          {
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${accessToken}`,
            },
          }
        );

        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: response.data.response,
            patientContext: response.data.patient_context || null,
          },
        ]);
      } catch (error) {
        console.error('Error:', error);
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: 'Mi dispiace, si è verificato un errore. Riprova.',
            isError: true,
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, messages, accessToken]
  );

  return {
    messages,
    input,
    setInput,
    isLoading,
    sendMessage,
    messagesEndRef,
    textareaRef,
  };
}
