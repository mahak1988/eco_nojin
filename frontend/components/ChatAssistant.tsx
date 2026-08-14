'use client';
import { useState } from 'react';
import { useI18n } from '../lib/i18n-context';
import { API_BASE } from '../lib/config';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Array<{
    title: string;
    source: string;
    relevance: number;
  }>;
}

export default function ChatAssistant() {
  const { t } = useI18n();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: input }),
      });

      if (!res.ok) throw new Error('API request failed');
      const data = await res.json();

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.message);
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: t('ai_unavailable') },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section
      aria-labelledby="chat-assistant-title"
      style={{
        marginTop: '32px',
        padding: '24px',
        border: '1px solid #ddd',
        borderRadius: '12px',
        background: '#f9f9f9',
      }}
    >
      <h2 id="chat-assistant-title" style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '16px', color: '#15803d' }}>
        🌱 {t('ai_assistant_title')}
      </h2>

      <div
        aria-live="polite"
        style={{
          maxHeight: '400px',
          overflowY: 'auto',
          marginBottom: '16px',
          padding: '12px',
          background: 'white',
          borderRadius: '8px',
          minHeight: '200px',
        }}
      >
        {messages.length === 0 && (
          <p style={{ color: '#666', textAlign: 'center', padding: '20px' }}>
            {t('chat_placeholder')}
          </p>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} style={{
            marginBottom: '12px',
            padding: '12px',
            borderRadius: '8px',
            background: msg.role === 'user' ? '#dcfce7' : '#f3f4f6',
            // User bubbles indent from the inline-start side (direction-aware)
            marginInlineStart: msg.role === 'user' ? '40px' : '0',
          }}>
            <strong>{msg.role === 'user' ? `👤 ${t('you_label')}` : `🤖 ${t('assistant_label')}`}</strong>
            <div style={{ whiteSpace: 'pre-wrap', marginTop: '4px' }}>{msg.content}</div>

            {msg.sources && msg.sources.length > 0 && (
              <div style={{
                marginTop: '8px',
                padding: '8px',
                background: 'white',
                borderRadius: '4px',
                fontSize: '0.85rem',
                color: '#666',
              }}>
                <strong>📚 {t('sources_label')}:</strong>
                <ul style={{ margin: '4px 0 0 0', paddingInlineStart: '20px' }}>
                  {msg.sources.map((src, i) => (
                    <li key={i}>
                      {src.title} — <em>{src.source}</em> ({t('relevance_label')}: {(src.relevance * 100).toFixed(0)}%)
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}

        {loading && <p style={{ color: '#2563eb' }}>{t('thinking')}</p>}
        {error && <p role="alert" style={{ color: '#dc2626' }}>{t('error_label')}: {error}</p>}
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
          placeholder={t('chat_placeholder')}
          aria-label={t('ai_assistant_title')}
          style={{
            flex: 1,
            padding: '12px',
            border: '1px solid #ccc',
            borderRadius: '8px',
            fontSize: '1rem',
          }}
        />
        <button
          onClick={sendMessage}
          disabled={loading || !input.trim()}
          aria-label={t('send_button')}
          style={{
            padding: '12px 24px',
            background: loading ? '#9ca3af' : '#15803d',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '1rem',
            cursor: loading ? 'not-allowed' : 'pointer',
          }}
        >
          {t('send_button')}
        </button>
      </div>
    </section>
  );
}
