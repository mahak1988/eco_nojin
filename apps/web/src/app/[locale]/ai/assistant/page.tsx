'use client';

import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { type FormEvent, useEffect, useRef, useState } from 'react';
import { ListBlock } from '@/components/ListBlock';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

const CHAT_PATH = '/api/v1/ai/chat';

/** Language codes accepted by the gateway QueryRequest contract. */
const SUPPORTED_LANGUAGES = new Set([
  'fa',
  'en',
  'ar',
  'ur',
  'de',
  'es',
  'fr',
  'hi',
  'it',
  'ms',
  'pt',
  'zh',
  'bn',
]);

type Source = { id: string; title: string; source: string; category: string; relevance: number };
type Citation = { slug?: string; reference?: string; doi?: string | null };
type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  confidence: number | null;
  sources: Source[];
  citations: Citation[];
};

function readDetail(data: unknown, fallback: string): string {
  if (data && typeof data === 'object') {
    const record = data as Record<string, unknown>;
    if (typeof record.detail === 'string') return record.detail;
    if (record.detail !== undefined) return fallback;
    if (typeof record.error === 'string') return record.error;
  }
  if (typeof data === 'string' && data.trim()) return data;
  return fallback;
}

export default function AssistantPage() {
  const t = useTranslations('ai');
  const common = useTranslations('common');
  const statusPage = useTranslations('statusPage');
  const pathname = usePathname();
  const locale = pathname.split('/')[1];

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    const question = input.trim();
    if (!question || isLoading) return;

    const userMessage: Message = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: question,
      confidence: null,
      sources: [],
      citations: [],
    };
    setMessages((previous) => [...previous, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(CHAT_PATH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Intent': '1' },
        credentials: 'same-origin',
        body: JSON.stringify(
          SUPPORTED_LANGUAGES.has(locale) ? { question, language: locale } : { question },
        ),
      });
      const data: unknown = await res.json().catch(() => null);

      if (!res.ok) throw new Error(readDetail(data, common('error')));

      const payload = (data ?? {}) as Record<string, unknown>;
      const answer = typeof payload.answer === 'string' ? payload.answer : '';
      if (!answer) throw new Error(common('error'));

      setMessages((previous) => [
        ...previous,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: answer,
          confidence: typeof payload.confidence === 'number' ? payload.confidence : null,
          sources: Array.isArray(payload.sources) ? (payload.sources as Source[]) : [],
          citations: Array.isArray(payload.citations) ? (payload.citations as Citation[]) : [],
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : common('error'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main id="main" className="min-h-dvh">
      <div className="mx-auto max-w-3xl px-6 pb-12 pt-8">
        <h1 className="display text-balance text-4xl font-bold text-ink">{t('title')}</h1>
        <p className="mt-3 max-w-2xl text-ink-soft">{t('lead')}</p>

        <div className="mt-4 flex flex-wrap items-center gap-3">
          <span className="chip num font-mono">{CHAT_PATH}</span>
          <ProvenanceStamp source={CHAT_PATH} label={CHAT_PATH} method={statusPage('state')} />
        </div>

        {error && (
          <div className="mt-6 card border-clay/40 p-4 text-sm" role="alert">
            <p className="font-medium text-clay">{common('error')}</p>
            <p className="mt-1 text-ink-soft">{error}</p>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="mt-2"
              onClick={() => setError(null)}
            >
              {common('retry')}
            </Button>
          </div>
        )}

        <Card density="cozy" className="mt-6 flex min-h-[400px] flex-col">
          <div className="flex-1 space-y-4" aria-live="polite">
            {messages.length === 0 && (
              <div className="py-8 text-center text-ink-soft">
                <p>{t('what')}</p>
              </div>
            )}
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-2xl p-4 text-sm ${
                    message.role === 'user'
                      ? 'rounded-br-md bg-forest text-paper'
                      : 'rounded-bl-md border border-line bg-surface text-ink'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  {message.role === 'assistant' &&
                    (message.confidence !== null ||
                      message.sources.length > 0 ||
                      message.citations.length > 0) && (
                      <div className="mt-3 flex flex-wrap items-center gap-2">
                        {message.confidence !== null && (
                          <span className="num chip font-mono text-[10px]">
                            {statusPage('result')}:{' '}
                            {new Intl.NumberFormat(locale === 'fa' ? 'fa-IR' : 'en', {
                              style: 'percent',
                              maximumFractionDigits: 0,
                            }).format(message.confidence)}
                          </span>
                        )}
                        {message.sources.map((source) => (
                          <ProvenanceStamp
                            key={`${message.id}-${source.id}`}
                            source={source.source || source.title || source.id}
                            label={source.title || source.id}
                          />
                        ))}
                        {message.citations.map((citation) => (
                          <ProvenanceStamp
                            key={`${message.id}-c-${citation.slug ?? citation.doi ?? citation.reference ?? ''}`}
                            source={citation.reference ?? citation.slug ?? ''}
                            label={citation.slug ?? citation.reference ?? ''}
                          />
                        ))}
                      </div>
                    )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="mt-4 border-t border-line pt-4">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                className="min-h-[60px] max-h-[200px] flex-1 resize-none rounded-md border border-line bg-background px-4 py-2 text-ink focus:outline-none focus:ring-2 focus:ring-forest"
                rows={1}
                disabled={isLoading}
                aria-label={t('audience')}
              />
              <Button
                type="submit"
                disabled={isLoading || !input.trim()}
                size="lg"
                loading={isLoading}
              >
                {common('view')}
              </Button>
            </form>
          </div>
        </Card>

        <div className="mt-6 grid gap-4">
          <ListBlock
            title={common('evidence')}
            items={t.raw('evidence') as string[]}
            tone="neutral"
          />
          <ListBlock title={common('limits')} items={t.raw('limits') as string[]} tone="clay" />
        </div>
      </div>
    </main>
  );
}
