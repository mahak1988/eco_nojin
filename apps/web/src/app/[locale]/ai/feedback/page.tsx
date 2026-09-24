'use client';

import { useState, FormEvent } from 'react';
import { useTranslations } from 'next-intl';
import { usePathname } from 'next/navigation';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Toast } from '@/components/ui/Toast';

interface FeedbackForm {
  rating: number;
  category: string;
  comment: string;
  email: string;
}

const CATEGORIES = [
  { value: 'accuracy', labelKey: 'feedback.category.accuracy' },
  { value: 'helpfulness', labelKey: 'feedback.category.helpfulness' },
  { value: 'tone', labelKey: 'feedback.category.tone' },
  { value: 'completeness', labelKey: 'feedback.category.completeness' },
  { value: 'other', labelKey: 'feedback.category.other' },
];

export default function FeedbackPage() {
  const t = useTranslations('ai.feedback');
  const common = useTranslations('common');
  const pathname = usePathname();
  const locale = pathname.split('/')[1];

  const [form, setForm] = useState<FeedbackForm>({
    rating: 0,
    category: '',
    comment: '',
    email: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (form.rating === 0 || !form.category || !form.comment.trim()) {
      setError(t('validationError'));
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setSubmitStatus('idle');

    try {
      const response = await fetch('/api/ai/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...form, locale }),
      });

      if (!response.ok) {
        throw new Error(t('submitError'));
      }

      setSubmitStatus('success');
      setForm({ rating: 0, category: '', comment: '', email: '' });
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
            <fieldset>
              <legend className="font-medium text-ink mb-3">{t('ratingLabel')}</legend>
              <div className="flex items-center gap-2" role="radiogroup" aria-label={t('ratingLabel')}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    type="button"
                    role="radio"
                    aria-checked={form.rating === star}
                    aria-label={`${star} ${t('starLabel')}`}
                    onClick={() => setForm((prev) => ({ ...prev, rating: star }))}
                    className="text-4xl transition-colors"
                    style={{ color: form.rating >= star ? 'var(--color-amber)' : 'var(--color-line)' }}
                  >
                    ★
                  </button>
                ))}
              </div>
              <p className="mt-2 text-sm text-ink-soft" aria-live="polite">
                {form.rating > 0 ? t(`rating.${form.rating}`) : t('rating.selectHint')}
              </p>
            </fieldset>

            <fieldset>
              <legend className="font-medium text-ink mb-3">{t('categoryLabel')}</legend>
              <div className="grid gap-2 sm:grid-cols-2" role="radiogroup" aria-label={t('categoryLabel')}>
                {CATEGORIES.map((cat) => (
                  <label
                    key={cat.value}
                    className={`relative cursor-pointer p-3 rounded-md border-2 transition-colors ${
                      form.category === cat.value
                        ? 'border-forest bg-forest/5'
                        : 'border-line hover:border-forest/50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="category"
                      value={cat.value}
                      checked={form.category === cat.value}
                      onChange={() => setForm((prev) => ({ ...prev, category: cat.value }))}
                      className="sr-only"
                    />
                    <span className="text-ink">{t(cat.labelKey)}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <div>
              <label htmlFor="comment" className="block font-medium text-ink mb-2">
                {t('commentLabel')}
              </label>
              <textarea
                id="comment"
                value={form.comment}
                onChange={(e) => setForm((prev) => ({ ...prev, comment: e.target.value }))}
                placeholder={t('commentPlaceholder')}
                rows={5}
                className="w-full px-4 py-3 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest resize-y min-h-[120px]"
                aria-describedby="comment-hint"
              />
              <p id="comment-hint" className="mt-1 text-sm text-ink-soft">{t('commentHint')}</p>
            </div>

            <div>
              <label htmlFor="email" className="block font-medium text-ink mb-2">
                {t('emailLabel')}
              </label>
              <input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
                placeholder={t('emailPlaceholder')}
                className="w-full px-4 py-3 rounded-md border border-line bg-background text-ink focus:outline-none focus:ring-2 focus:ring-forest"
                aria-describedby="email-hint"
              />
              <p id="email-hint" className="mt-1 text-sm text-ink-soft">{t('emailHint')}</p>
            </div>

            <div className="flex gap-3 pt-4">
              <Button type="submit" size="lg" disabled={isSubmitting} className="flex-1">
                {isSubmitting ? t('submitting') : t('submit')}
              </Button>
              <Button type="button" variant="secondary" size="lg" onClick={() => setForm({ rating: 0, category: '', comment: '', email: '' })}>
                Reset
              </Button>
            </div>

            <p className="text-center text-xs text-ink-soft">{t('disclaimer')}</p>
          </form>
        </Card>
      </div>
    </main>
  );
}