'use client';

import { useState, useRef, useEffect, FormEvent } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname, useRouter } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { ProvenanceStamp } from '@/components/ProvenanceStamp';
import { Card } from '@/components/ui/Card';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: string[];
  timestamp: Date;
}

export default function AssistantPage() {
  const t = useTranslations('ai.assistant');
  const common = useTranslations('common');
  const pathname = usePathname();
  const locale = pathname.split('/')[1];

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/ai/assistant`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.content, locale }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error ?? t('error'));
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        sources: data.sources,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('error'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-3xl px-4 py-8">
        <header className="mb-8">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-2 text-ink-soft">{t('lead')}</p>
        </header>

        {error && (
          <div className="mb-6 p-4 rounded-md bg-red-50 border border-red-200 text-red-700" role="alert">
            {error}
            <Button variant="ghost" size="sm" className="ml-2" onClick={() => setError(null)}>
              Try again
            </Button>
          </div>
        )}

        <Card density="cozy" className="flex flex-col h-[calc(100vh-20rem)] min-h-[400px]">
          <div className="flex-1 overflow-y-auto p-4 space-y-4" aria-live="polite">
            {messages.length === 0 && (
              <div className="text-center text-ink-soft py-8">
                <p>{t('welcome')}</p>
                <p className="mt-2 text-sm">{t('welcomeHint')}</p>
              </div>
            )}
            {messages.map((msg) => (
              <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[80%] ${msg.role === 'user' ? 'bg-forest text-paper' : 'bg-surface border border-line'}`}>
                  <div className="p-4">
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {msg.sources.map((source, idx) => (
                          <ProvenanceStamp key={idx} source={source} label={`[${idx + 1}]`} />
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="border-t border-line p-4">
            <form onSubmit={handleSubmit} className="flex gap-2">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={t('placeholder')}
                className="flex-1 min-h-[60px] max-h-[200px] px-4 py-2 rounded-md border border-line bg-background text-ink resize-none focus:outline-none focus:ring-2 focus:ring-forest"
                rows={1}
                disabled={isLoading}
                aria-label={t('placeholder')}
              />
              <Button type="submit" disabled={isLoading || !input.trim()} size="lg" aria-label={t('sendLabel')}>
                {isLoading ? t('sending') : t('send')}
              </Button>
            </form>
            <p className="mt-2 text-xs text-ink-soft text-center">{t('disclaimer')}</p>
          </div>
        </Card>
      </div>
    </main>
  );
}