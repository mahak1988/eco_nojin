'use client';

import { useTranslations } from 'next-intl';
import { useState } from 'react';
import { Button } from '@/components/ui/Button';

type SubmitState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'done'; status: number }
  | { kind: 'failed'; status: number; detail: string };

/**
 * Posts to a registered gateway route. There is no local-only branch: a
 * non-2xx response is surfaced verbatim instead of being reported as success.
 */
export function EndpointForm({
  path,
  fields,
  submitLabel,
  consentLabel,
}: {
  path: string;
  fields: { name: string; label: string; type: string; required: boolean }[];
  submitLabel: string;
  consentLabel: string;
}) {
  const common = useTranslations('common');
  const status = useTranslations('statusLine');
  const [state, setState] = useState<SubmitState>({ kind: 'idle' });

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(
      fields
        .map((field) => [field.name, String(form.get(field.name) ?? '').trim()])
        .filter(([, value]) => value !== ''),
    );
    if (Object.keys(payload).length === 0) {
      setState({ kind: 'failed', status: 0, detail: path });
      return;
    }
    setState({ kind: 'loading' });
    try {
      const response = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (response.ok) {
        setState({ kind: 'done', status: response.status });
        return;
      }
      const detail = await response.text();
      setState({ kind: 'failed', status: response.status, detail: detail.slice(0, 200) });
    } catch {
      setState({ kind: 'failed', status: 0, detail: path });
    }
  }

  return (
    <form className="space-y-4" onSubmit={handleSubmit} noValidate>
      {fields.map((field) => (
        <div key={field.name}>
          <label htmlFor={`field-${field.name}`} className="block text-sm text-ink-soft mb-1">
            {field.label}
          </label>
          <input
            id={`field-${field.name}`}
            name={field.name}
            type={field.type}
            required={field.required}
            className="w-full px-4 py-2 rounded border border-line bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-forest"
          />
        </div>
      ))}
      <Button variant="primary" type="submit" loading={state.kind === 'loading'}>
        {submitLabel}
      </Button>
      <p className="text-xs text-ink-soft">{consentLabel}</p>
      {state.kind === 'done' ? (
        <p className="text-sm text-forest" role="status">
          {common('live')} · {path} · {state.status}
        </p>
      ) : null}
      {state.kind === 'failed' ? (
        <p className="text-sm text-copper" role="alert">
          {common('error')} · {path} · {state.status || '—'} · {state.detail} ·{' '}
          {status('unavailable')}
        </p>
      ) : null}
    </form>
  );
}
