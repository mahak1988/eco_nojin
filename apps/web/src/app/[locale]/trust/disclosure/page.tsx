'use client';

import { useState, FormEvent } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Toast } from '@/components/ui/Toast';

interface DisclosureForm {
  type: string;
  severity: string;
  title: string;
  description: string;
  contact: string;
  pgpKey?: string;
}

export default function DisclosurePage() {
  const t = useTranslations('trust.disclosure');
  const common = useTranslations('common');
  const pathname = usePathname();
  const locale = pathname.split('/')[1];

  const [form, setForm] = useState<DisclosureForm>({
    type: '',
    severity: '',
    title: '',
    description: '',
    contact: '',
    pgpKey: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!form.type || !form.severity || !form.title || !form.description || !form.contact) {
      setError(t('validationError'));
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSubmitStatus('idle');

    try {
      const res = await fetch('/api/trust/disclosure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, locale }),
      });

      if (!res.ok) throw new Error(t('submitError'));

      setSubmitStatus('success');
      setForm({ type: '', severity: '', title: '', description: '', contact: '', pgpKey: '' });
    } catch {
      setSubmitStatus('error');
      setError(t('submitError'));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main id="main" className="min-h-screen">
      <div className="mx-auto max-w-2xl px-4 py-10">
        <header className="mb-10">
          <h1 className="display text-3xl font-bold text-ink sm:text-4xl">{t('title')}</h1>
          <p className="mt-3 text-ink-soft">{t('lead')}</p>
        </header>

        {submitStatus === 'success' && (
          <Toast variant="success" title={t('successTitle')} className="mb-6" onClose={() => setSubmitStatus('idle')}>
            {t('successMessage')}
          </Toast>
        )}

        {submitStatus === 'error' && (
          <Toast variant="error" title={t('errorTitle')} className="mb-6" onClose={() => setSubmitStatus('idle')}>
            {t('errorMessage')}
          </Toast>
        )}

        {error && (
          <div className="mb-6 p-4 rounded-md bg-red-50 border border-red-200 text-red-700" role="alert">
            {error}
            <Button variant="ghost" size="sm" className="ml-2" onClick={() => setError(null)}>
              Try again
            </Button>
          </div>
        )}

        <Card density="cozy">
          <form onSubmit={handleSubmit} className="space-y-6" noValidate>
            <div>
              <label htmlFor="type" className="block font-medium text-ink mb-2">
                {t('typeLabel')}
              </label>
              <select
                id="type"
                value={form.type}
                onChange={e => setForm(prev => ({ ...prev, type: e.target.value }))}
                className="w-full px-4 py-3 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest"
                required
              >
                <option value="">{t('typeSelect')}</option>
                <option value="vulnerability">{t('type.vulnerability')}</option>
                <option value="privacy">{t('type.privacy')}</option>
                <option value="security">{t('type.security')}</option>
                <option value="other">{t('type.other')}</option>
              </select>
            </div>

            <div>
              <label htmlFor="severity" className="block font-medium text-ink mb-2">
                {t('severityLabel')}
              </label>
              <select
                id="severity"
                value={form.severity}
                onChange={e => setForm(prev => ({ ...prev, severity: e.target.value }))}
                className="w-full px-4 py-3 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest"
                required
              >
                <option value="">{t('severitySelect')}</option>
                <option value="critical">{t('severity.critical')}</option>
                <option value="high">{t('severity.high')}</option>
                <option value="medium">{t('severity.medium')}</option>
                <option value="low">{t('severity.low')}</option>
              </select>
            </div>

            <div>
              <label htmlFor="title" className="block font-medium text-ink mb-2">
                {t('titleLabel')}
              </label>
              <input
                id="title"
                type="text"
                value={form.title}
                onChange={e => setForm(prev => ({ ...prev, title: e.target.value }))}
                placeholder={t('titlePlaceholder')}
                className="w-full px-4 py-3 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest"
                required
              />
            </div>

            <div>
              <label htmlFor="description" className="block font-medium text-ink mb-2">
                {t('descriptionLabel')}
              </label>
              <textarea
                id="description"
                value={form.description}
                onChange={e => setForm(prev => ({ ...prev, description: e.target.value }))}
                placeholder={t('descriptionPlaceholder')}
                rows={6}
                className="w-full px-4 py-3 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest resize-y min-h-[150px]"
                required
              />
            </div>

            <div>
              <label htmlFor="contact" className="block font-medium text-ink mb-2">
                {t('contactLabel')}
              </label>
              <input
                id="contact"
                type="email"
                value={form.contact}
                onChange={e => setForm(prev => ({ ...prev, contact: e.target.value }))}
                placeholder={t('contactPlaceholder')}
                className="w-full px-4 py-3 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest"
                required
              />
              <p className="mt-1 text-sm text-ink-soft">{t('contactHint')}</p>
            </div>

            <div>
              <label htmlFor="pgpKey" className="block font-medium text-ink mb-2">
                {t('pgpKeyLabel')}
              </label>
              <textarea
                id="pgpKey"
                value={form.pgpKey}
                onChange={e => setForm(prev => ({ ...prev, pgpKey: e.target.value }))}
                placeholder={t('pgpKeyPlaceholder')}
                rows={4}
                className="w-full px-4 py-3 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest font-mono text-sm resize-y"
              />
              <p className="mt-1 text-sm text-ink-soft">{t('pgpKeyHint')}</p>
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" size="lg" disabled={isSubmitting} className="flex-1">
                {isSubmitting ? t('submitting') : t('submit')}
              </Button>
              <Button type="button" variant="secondary" size="lg" onClick={() => setForm({ type: '', severity: '', title: '', description: '', contact: '', pgpKey: '' })}>
                Reset
              </Button>
            </div>

            <p className="text-center text-xs text-ink-soft">{t('disclaimer')}</p>
          </form>
        </Card>

        <Card density="cozy" className="mt-6">
          <h2 className="font-medium text-ink mb-3">{t('pgpPublicKey')}</h2>
          <pre className="bg-surface-2 border border-line rounded-md p-4 text-xs font-mono overflow-x-auto text-ink-soft">
            {t('pgpKeyContent')}
          </pre>
          <p className="mt-2 text-sm text-ink-soft">{t('pgpKeyNote')}</p>
        </Card>
      </div>
    </main>
  );
}