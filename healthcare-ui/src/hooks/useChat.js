import { useState, useRef, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function useChat() {
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
        const response = await axios.post(
          `${API_URL}/chat`,
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
              'ngrok-skip-browser-warning': 'true',
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
    [isLoading, messages]
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
