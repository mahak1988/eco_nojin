/** Advisory chat runner — wraps the AI advice endpoint (RAG → NLG).
 * Reuses the dashboard glass/panel style and IndexRunner patterns. */

import { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Loader2, Sparkles, MessageSquare, Copy, Check } from 'lucide-react';
import { useLang } from '../../i18n/LanguageContext';
import { useAdvisory, type AdviceEvidence } from '../../lib/advisory';
import Reveal from '../ui/Reveal';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  evidence?: AdviceEvidence[];
  metrics?: Record<string, number>;
  timestamp: Date;
}

export default function AdvisoryRunner({
  lat,
  lon,
  className,
}: {
  lat?: number;
  lon?: number;
  className?: string;
}) {
  const { lang } = useLang();
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, error, isFetching } = useAdvisory(input, lat, lon);
  const lastQuestionRef = useRef('');

  useEffect(() => {
    if (input && input !== lastQuestionRef.current && data?.status === 'ok') {
      lastQuestionRef.current = input;
      setMessages((prev) => [
        ...prev,
        {
          id: `user-${Date.now()}`,
          role: 'user',
          content: input,
          timestamp: new Date(),
        },
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: data.answer ?? '',
          evidence: data.evidence,
          metrics: data.metrics,
          timestamp: new Date(),
        },
      ]);
      setInput('');
    }
  }, [data, input]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = useCallback(
    (event: React.FormEvent) => {
      event.preventDefault();
      const q = input.trim();
      if (!q) return;
      if (q.length < 3) return;
      lastQuestionRef.current = '';
      setInput(q);
    },
    [input],
  );

  const handleCopy = useCallback(async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {
      /* clipboard unavailable */
    }
  }, []);

  const isFa = lang === 'fa';

  return (
    <div className={`flex flex-col gap-4 ${className || ''}`}>
      <Reveal>
        <div className="glass rounded-2xl p-5">
          <div className="flex items-center gap-3 mb-4">
            <Sparkles className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
            <h3 className="text-base font-extrabold text-[var(--color-night-100)]">
              {isFa ? 'مشاور هوشمند کشاورزی' : 'AI Farm Advisor'}
            </h3>
            <span className="ml-auto text-[10px] font-bold text-[var(--color-night-200)]/35">
              {isFa ? 'RAG + NLG' : 'Powered by RAG'}
            </span>
          </div>

          {messages.length === 0 ? (
            <div className="text-center py-8">
              <MessageSquare className="h-8 w-8 mx-auto mb-3 text-[var(--color-night-200)]/20" aria-hidden />
              <p className="text-sm text-[var(--color-night-200)]/50">
                {isFa ? 'سؤال کشاورزی خود را بپرسید…' : 'Ask your farming question…'}
              </p>
              <p className="text-[10px] text-[var(--color-night-200)]/30 mt-1">
                {isFa ? 'مثال: چه محصولی در خاک شنی باید کشت شود؟' : 'e.g. What crop for sandy soil?'}
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-3 max-h-[480px] overflow-y-auto pr-1">
              <AnimatePresence initial={false}>
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-6 ${
                        msg.role === 'user'
                          ? 'bg-[var(--color-leaf-500)]/15 text-[var(--color-night-100)]'
                          : 'glass text-[var(--color-night-100)]'
                      }`}
                      dir="ltr"
                    >
                      {msg.role === 'user' ? (
                        <p>{msg.content}</p>
                      ) : (
                        <div>
                          <p className="whitespace-pre-wrap">{msg.content}</p>

                          {msg.metrics && Object.keys(msg.metrics).length > 0 ? (
                            <div className="mt-3 flex flex-wrap gap-1.5">
                              {Object.entries(msg.metrics).map(([key, value]) => (
                                <span
                                  key={key}
                                  className="rounded-full bg-[var(--color-aqua-500)]/15 px-2 py-0.5 text-[10px] font-bold text-[var(--color-aqua-300)]"
                                  dir="ltr"
                                >
                                  {key}: {value}
                                </span>
                              ))}
                            </div>
                          ) : null}

                          {msg.evidence && msg.evidence.length > 0 ? (
                            <div className="mt-3 border-t border-white/5 pt-2">
                              <p className="text-[10px] font-bold text-[var(--color-night-200)]/40 mb-1">
                                {isFa ? 'منابع:' : 'Sources:'}
                              </p>
                              <ul className="flex flex-col gap-1">
                                {msg.evidence.map((ev, i) => (
                                  <li key={i} className="text-[10px] text-[var(--color-night-200)]/50" dir="ltr">
                                    {ev.type === 'rag' ? '📄 ' : ev.type === 'metric_alert' ? '📊 ' : '📚 '}
                                    {ev.source}: {ev.content.slice(0, 150)}
                                    {ev.content.length > 150 ? '…' : ''}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ) : null}

                          <div className="flex items-center gap-2 mt-2">
                            <button
                              type="button"
                              onClick={() => handleCopy(msg.content, msg.id)}
                              className="inline-flex items-center gap-1 text-[10px] font-bold text-[var(--color-night-200)]/40 hover:text-[var(--color-night-200)]/70"
                            >
                              {copiedId === msg.id ? (
                                <Check className="h-3 w-3 text-[var(--color-leaf-400)]" aria-hidden />
                              ) : (
                                <Copy className="h-3 w-3" aria-hidden />
                              )}
                              {copiedId === msg.id ? (isFa ? 'کپی شد' : 'Copied') : (isFa ? 'کپی' : 'Copy')}
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {(isFetching || isLoading) && (
                <div className="flex justify-start">
                  <div className="glass rounded-2xl px-4 py-3 flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin text-[var(--color-leaf-400)]" aria-hidden />
                    <span className="text-xs text-[var(--color-night-200)]/50">
                      {isFa ? 'در حال تحلیل…' : 'Analyzing…'}
                    </span>
                  </div>
                </div>
              )}

              {error ? (
                <div className="rounded-2xl border border-red-400/30 bg-red-400/10 p-3 text-xs font-bold text-red-300" role="alert">
                  {isFa ? 'خطا در دریافت مشاوره' : 'Error fetching advice'}
                  <p className="mt-1 font-normal text-red-300/70" dir="ltr">{error.message}</p>
                </div>
              ) : null}

              <div ref={bottomRef} />
            </div>
          )}

          <form onSubmit={handleSubmit} className="mt-4 flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={isFa ? 'سؤال کشاورزی خود را بنویسید…' : 'Ask a farming question…'}
              className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-[var(--color-night-100)] outline-none focus:border-[var(--color-leaf-400)]"
              dir="ltr"
            />
            <button
              type="submit"
              disabled={input.trim().length < 3 || isFetching || isLoading}
              className="inline-flex items-center gap-2 rounded-xl bg-[var(--color-leaf-500)] px-4 py-2.5 text-sm font-extrabold text-white transition hover:bg-[var(--color-leaf-400)] disabled:cursor-not-allowed disabled:opacity-60"
            >
              <Send className="h-4 w-4" aria-hidden />
              {isFa ? 'ارسال' : 'Send'}
            </button>
          </form>
        </div>
      </Reveal>
    </div>
  );
}
