import React, { useState } from 'react';
import { Bot, Send, BookOpen } from 'lucide-react';

interface AdviceResult {
  status?: string;
  provider?: string;
  answer?: string;
  evidence?: { file?: string; title?: string }[];
  metrics?: { spi?: number | null };
  note?: string;
  error?: string;
}

/**
 * فاز ۸-ج — توصیه هوشمند طبیعی (RAG → NLG/LLM).
 * پیش‌فرض: موتور محلی رایگان (صادقانه برچسب‌خورده)؛ با AI_LLM_KEY به LLM واقعی ارتقا می‌یابد.
 */
export const AiAdviceCard: React.FC = () => {
  const [question, setQuestion] = useState('بندسار برای کاهش رواناب و خشکسالی چقدر موثر است؟');
  const [result, setResult] = useState<AdviceResult | null>(null);
  const [status, setStatus] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle');

  const ask = async () => {
    if (!question.trim()) return;
    setStatus('loading');
    try {
      const res = await fetch('/api/v1/ai/advise', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim(), lat: 35.7, lon: 51.4 }),
      });
      const d = (await res.json()) as AdviceResult;
      if (d.status === 'ok') {
        setResult(d);
        setStatus('ok');
      } else {
        setStatus('error');
        setResult({ error: String(d.error ?? 'خطا') });
      }
    } catch (e) {
      setStatus('error');
      setResult({ error: e instanceof Error ? e.message : 'خطا' });
    }
  };

  return (
    <div className="card" style={{ padding: '1.1rem', marginTop: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.7rem' }}>
        <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#0d9488' }}>
          <Bot size={17} /> توصیه هوشمند (RAG → NLG/LLM)
        </h3>
        {status === 'ok' && result?.provider && (
          <span style={{ fontSize: '0.68rem', padding: '0.2rem 0.55rem', borderRadius: 999, background: 'var(--color-bg)', border: '1px solid var(--color-border)', color: 'var(--color-text-secondary)' }}>
            موتور: {result.provider}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', gap: '0.35rem' }}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && void ask()}
          style={{ flex: 1, padding: '0.4rem 0.6rem', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', fontSize: '0.78rem' }}
        />
        <button onClick={() => void ask()} disabled={status === 'loading'} style={{ padding: '0.4rem 0.9rem', borderRadius: 8, border: 'none', cursor: 'pointer', background: 'var(--color-primary)', color: '#fff', fontWeight: 700, fontSize: '0.75rem', display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
          <Send size={12} /> {status === 'loading' ? '…' : 'بپرس'}
        </button>
      </div>

      {status === 'error' && <p style={{ fontSize: '0.8rem', color: '#ef4444', margin: '0.6rem 0 0' }}>⚠️ {result?.error}</p>}

      {status === 'ok' && result?.answer && (
        <div style={{ marginTop: '0.7rem', padding: '0.7rem 0.8rem', borderRadius: 10, border: '1px solid var(--color-border)', background: 'var(--color-bg)', whiteSpace: 'pre-line', fontSize: '0.8rem', color: 'var(--color-text)' }}>
          {result.answer}
          {result.metrics?.spi != null && (
            <span style={{ display: 'inline-block', marginTop: '0.3rem', fontSize: '0.7rem', color: '#0d9488', fontWeight: 700 }}>
              {' '}· SPI زنده: {result.metrics.spi}
            </span>
          )}
          {result.evidence && result.evidence.length > 0 && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.68rem', color: 'var(--color-text-secondary)', display: 'flex', alignItems: 'flex-start', gap: '0.3rem' }}>
              <BookOpen size={11} style={{ marginTop: 2, flexShrink: 0 }} />
              <span>شواهد: {result.evidence.map((e) => e.file).join('، ')}</span>
            </div>
          )}
          {result.note && <p style={{ fontSize: '0.66rem', color: 'var(--color-text-secondary)', margin: '0.5rem 0 0' }}>{result.note}</p>}
        </div>
      )}
    </div>
  );
};
