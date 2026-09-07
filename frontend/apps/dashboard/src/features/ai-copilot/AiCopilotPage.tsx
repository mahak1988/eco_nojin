import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@eco/api/mutator';
import { Alert, Button, Card, CardBody, CardHeader, Input, Spinner } from '@eco/ui';

type ChatResult = {
  response?: string;
  message?: string;
  model?: string;
  tokens?: number;
  [key: string]: unknown;
};

export function AiCopilotPage() {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [history, setHistory] = useState<Array<{ role: 'user' | 'assistant'; text: string; meta?: ChatResult }>>([]);

  const chat = useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post<ChatResult>('/ai/chat', {
        message: query,
      });
      return data;
    },
    onSuccess: (data) => {
      const text = data.response ?? data.message ?? t('dashboard.pages.ai-copilot.noResponse', 'No response from backend');
      setHistory((prev) => [
        ...prev,
        { role: 'user', text: query },
        { role: 'assistant', text, meta: data },
      ]);
      setQuery('');
    },
  });

  const ask = () => {
    if (!query.trim()) return;
    chat.mutate();
  };

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="text-2xl font-semibold">{t('dashboard.pages.ai-copilot.title', '🤖 AI Copilot')}</h1>
        <p className="text-sm text-ink-muted">
          {t('dashboard.pages.ai-copilot.subtitle', 'Ask scientific questions in natural language via')}{' '}
          <code className="rounded bg-surface-muted px-1">/ai/chat</code>
          {t('dashboard.pages.ai-copilot.subtitlePeriod', '.')}
        </p>
      </header>

      <Card>
        <CardHeader>
          <h2 className="text-base font-semibold">{t('dashboard.pages.ai-copilot.conversation', 'Conversation')}</h2>
        </CardHeader>
        <CardBody className="flex flex-col gap-3">
          <div className="flex max-h-96 flex-col gap-3 overflow-y-auto rounded bg-surface-muted p-3">
            {history.length === 0 ? (
              <p className="py-12 text-center text-sm text-ink-muted">
                {t('dashboard.pages.ai-copilot.emptyState', 'Ask a question to start the conversation.')}
              </p>
            ) : (
              history.map((msg, idx) => (
                <div
                  key={`${msg.role}-${idx}`}
                  className={
                    msg.role === 'user'
                      ? 'ms-auto max-w-[80%] rounded-md bg-brand-600 px-3 py-2 text-sm text-white'
                      : 'me-auto max-w-[80%] rounded-md bg-surface-raised px-3 py-2 text-sm text-ink shadow-soft'
                  }
                >
                  <div className="mb-1 text-[10px] uppercase tracking-wide opacity-70">
                    {msg.role === 'user' ? t('dashboard.pages.ai-copilot.you', 'You') : t('dashboard.pages.ai-copilot.copilot', 'Copilot')}
                  </div>
                  <div className="whitespace-pre-wrap">{msg.text}</div>
                </div>
              ))
            )}
          </div>

          <div className="flex gap-2">
            <Input
              placeholder={t('dashboard.pages.ai-copilot.inputPlaceholder', "e.g. What's the best cover crop for dryland wheat?")}
              value={query}
              onChange={(e) => setQuery((e.target as HTMLInputElement).value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  ask();
                }
              }}
              disabled={chat.isPending}
            />
            <Button onClick={ask} disabled={chat.isPending || !query.trim()}>
              {chat.isPending ? <Spinner size="sm" tone="inverse" /> : null}
              {t('dashboard.pages.ai-copilot.ask', 'Ask')}
            </Button>
          </div>

          {chat.error && (
            <Alert tone="danger" title={t('dashboard.pages.ai-copilot.errorTitle', 'Copilot error')}>
              {(chat.error as Error).message}
            </Alert>
          )}
        </CardBody>
      </Card>
    </div>
  );
}