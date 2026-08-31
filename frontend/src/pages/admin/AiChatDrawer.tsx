import { useEffect, useRef, useState } from 'react';
import { Bot, MessageSquare, Send, User, X } from 'lucide-react';

const API_BASE = 'http://localhost:8000/api/v1';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  provider?: string;
  error?: boolean;
}

/**
 * شناور: دستیار هوشمند ادمین — چت فارسی RTL با موتور AI محلی (Ollama)
 * Backend: POST /api/v1/admin/ai/chat  (admin-only, audited)
 */
export default function AiChatDrawer() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        'سلام! من دستیار هوشمند ادمین هستم و به داده‌های زنده‌ی پلتفرم دسترسی دارم.\nدرباره‌ی کاربران، خطاها، مزارع، تحلیل‌ها یا وضعیت امنیتی بپرسید.',
    },
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [messages, sending, open]);

  const send = async () => {
    const q = input.trim();
    if (!q || sending) return;
    setInput('');
    setMessages((m) => [...m, { role: 'user', content: q }]);
    setSending(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + '/admin/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ question: q, page: window.location.pathname }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: data.answer, provider: data.provider },
      ]);
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content: 'خطا در ارتباط با دستیار. مطمئن شوید بک‌اند و Ollama فعال هستند.',
          error: true,
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  return (
    <>
      {!open && (
        <button
          onClick={() => setOpen(true)}
          title="دستیار هوشمند ادمین"
          style={{
            position: 'fixed',
            bottom: '24px',
            left: '24px',
            zIndex: 1200,
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            border: 'none',
            cursor: 'pointer',
            background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 8px 24px rgba(99, 102, 241, 0.4)',
          }}
        >
          <MessageSquare size={24} />
        </button>
      )}

      {open && (
        <div
          dir="rtl"
          style={{
            position: 'fixed',
            bottom: '24px',
            left: '24px',
            zIndex: 1200,
            width: 'min(420px, calc(100vw - 32px))',
            height: 'min(560px, calc(100vh - 48px))',
            borderRadius: '16px',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            background: 'var(--bg-card-solid, #16181f)',
            border: '1px solid var(--border-color, #2a2d38)',
            boxShadow: '0 16px 48px rgba(0,0,0,0.5)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '14px 16px',
              background: 'linear-gradient(135deg, rgba(139,92,246,0.25), rgba(99,102,241,0.15))',
              borderBottom: '1px solid var(--border-color, #2a2d38)',
              fontWeight: 600,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Bot size={20} style={{ color: 'var(--accent-purple, #8b5cf6)' }} />
              <span>دستیار هوشمند ادمین</span>
              <span
                style={{
                  fontSize: '10px',
                  padding: '2px 8px',
                  borderRadius: '10px',
                  background: 'rgba(16,185,129,0.15)',
                  color: '#10b981',
                }}
              >
                محلی • آفلاین
              </span>
            </div>
            <button
              onClick={() => setOpen(false)}
              style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer' }}
              title="بستن"
            >
              <X size={18} />
            </button>
          </div>

          <div
            ref={bodyRef}
            style={{
              flex: 1,
              overflowY: 'auto',
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            {messages.map((m, i) => (
              <div
                key={i}
                style={{
                  display: 'flex',
                  flexDirection: m.role === 'user' ? 'row-reverse' : 'row',
                  gap: '8px',
                  alignItems: 'flex-start',
                }}
              >
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '8px',
                    flexShrink: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: m.role === 'user' ? 'rgba(59,130,246,0.2)' : 'rgba(139,92,246,0.2)',
                    color: m.role === 'user' ? '#3b82f6' : '#8b5cf6',
                  }}
                >
                  {m.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>
                <div
                  style={{
                    maxWidth: '80%',
                    padding: '10px 12px',
                    borderRadius: '12px',
                    whiteSpace: 'pre-wrap',
                    lineHeight: 1.7,
                    fontSize: '13px',
                    background: m.error
                      ? 'rgba(239,68,68,0.12)'
                      : m.role === 'user'
                        ? 'rgba(59,130,246,0.15)'
                        : 'var(--bg-hover, rgba(255,255,255,0.04))',
                    border: m.error
                      ? '1px solid rgba(239,68,68,0.3)'
                      : '1px solid var(--border-color, #2a2d38)',
                  }}
                >
                  {m.content}
                  {m.provider && (
                    <div
                      style={{
                        marginTop: '6px',
                        fontSize: '10px',
                        opacity: 0.55,
                        direction: 'ltr',
                        textAlign: 'left',
                      }}
                    >
                      {m.provider}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center', opacity: 0.7 }}>
                <Bot size={14} style={{ color: '#8b5cf6' }} />
                <span style={{ fontSize: '12px' }}>در حال فکر کردن… (مدل محلی روی CPU)</span>
              </div>
            )}
          </div>

          <div
            style={{
              display: 'flex',
              gap: '8px',
              padding: '12px',
              borderTop: '1px solid var(--border-color, #2a2d38)',
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') send();
              }}
              placeholder="سوال خود را بپرسید…"
              disabled={sending}
              style={{
                flex: 1,
                padding: '10px 14px',
                borderRadius: '10px',
                border: '1px solid var(--border-color, #2a2d38)',
                background: 'var(--bg-hover, rgba(255,255,255,0.04))',
                color: 'var(--text-primary, #e5e7eb)',
                fontSize: '13px',
                outline: 'none',
              }}
            />
            <button
              onClick={send}
              disabled={sending || !input.trim()}
              style={{
                width: '42px',
                borderRadius: '10px',
                border: 'none',
                cursor: sending || !input.trim() ? 'default' : 'pointer',
                background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
                color: '#fff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                opacity: sending || !input.trim() ? 0.5 : 1,
              }}
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
