import React, { useState } from 'react';
import axios from 'axios';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

const apiBase = () => (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000');

export const LLMChatWidget: React.FC<{ houseId: string; houseData?: any }> = ({ houseId, houseData }) => {
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant'; text: string }[]>([
    {
      role: 'assistant',
      text: `👋 Привет! Я — ИИ-помощник МВК (Мосводоканал) для дома ${houseData?.simple_address || houseData?.address || 'неизвестного'}.\nМогу объяснить статус дома, дать рекомендации по устранению неполадок и помочь с анализом данных по этому дому.`
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!inputValue.trim()) return;
    const userMessage = inputValue.trim();
    setMessages(prev => [...prev, { role: 'user', text: userMessage }]);
    setInputValue('');
    setIsLoading(true);

    try {
      const base = apiBase();
      const response = await axios.post(`${base}/api/houses/${houseId}/ask-llm`, {
        question: userMessage
      });
      setMessages(prev => [...prev, { role: 'assistant', text: response.data.answer || 'Без ответа.' }]);
    } catch (error: any) {
      console.error('LLM error:', error);
      const errorMsg = error.response?.data?.detail || 'Не удалось получить ответ от модели.';
      setMessages(prev => [...prev, { role: 'assistant', text: errorMsg }]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleOpen = () => setIsOpen(!isOpen);

  return (
    <>
      <button
        className="button primary"
        onClick={toggleOpen}
        title="ИИ-помощник МВК"
        style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          width: 56,
          height: 56,
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
          zIndex: 1000,
        }}
      >
        💬
      </button>

      {isOpen && (
        <div
          style={{
            position: 'fixed',
            bottom: 84,
            right: 24,
            width: 360,
            maxHeight: 500,
            backgroundColor: 'var(--bg)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: 8,
            boxShadow: '0 6px 20px rgba(0,0,0,0.4)',
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            zIndex: 1000,
          }}
        >
          <div
            style={{
              padding: 12,
              backgroundColor: 'rgba(255,255,255,0.03)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ fontWeight: 500, fontSize: 14 }}>Умный помощник МВК</span>
            <button className="button ghost" onClick={toggleOpen} style={{ padding: 4 }}>
              ✕
            </button>
          </div>

          <div
            style={{
              flex: 1,
              padding: 12,
              overflowY: 'auto',
              fontSize: 13,
            }}
          >
            {messages.map((msg, i) => (
              <div key={i} style={{ margin: '6px 0' }}>
                <div style={{
                  fontWeight: 'bold',
                  color: msg.role === 'assistant' ? 'var(--primary)' : 'var(--primary-2)'
                }}>
                  {msg.role === 'assistant' ? 'ИИ-ассистент:' : 'Вы:'}
                </div>
                <div
                  dangerouslySetInnerHTML={{
                    __html: DOMPurify.sanitize(
                      marked.parse(msg.text, { breaks: true }) as string
                    )
                  }}
                  style={{ marginTop: 4, lineHeight: 1.4 }}
                />
              </div>
            ))}
            {isLoading && <div style={{
              fontWeight: 'bold',
              color: 'var(--primary)'
            }}>Генерация ответа...</div>}
          </div>

          <div style={{ padding: 12, borderTop: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ display: 'flex', gap: 6 }}>
              <input
                className="input"
                placeholder="Ваш вопрос..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                style={{ flex: 1, fontSize: 13 }}
              />
              <button className="button primary" onClick={sendMessage} disabled={isLoading}>
                Отправить
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};