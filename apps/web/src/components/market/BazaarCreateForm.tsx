'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { type FormEvent, useState } from 'react';
import { useAuth } from '@/components/providers/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { createBazaar } from '@/lib/api/market';
import { type BazaarCreateInput, bazaarCreateSchema } from '@/lib/validation/bazaar-create';

const EMPTY_FORM: BazaarCreateInput = {
  name: '',
  marketplaceType: 'cooperative',
  description: '',
  address: '',
  location: '',
  villageId: '',
  acceptEcommerce: false,
  acceptTrading: false,
  rulesDocument: '',
  contactEmail: '',
  contactPhone: '',
};

export function BazaarCreateForm() {
  const t = useTranslations('market.bazaarCreate');
  const pathname = usePathname();
  const locale = pathname.split('/')[1] || 'fa';
  const { user, loading: authLoading } = useAuth();

  const [form, setForm] = useState(EMPTY_FORM);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [detail, setDetail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [createdId, setCreatedId] = useState('');

  const update = <K extends keyof BazaarCreateInput>(key: K, value: BazaarCreateInput[K]) => {
    setForm((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: '' }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (authLoading) return;
    if (!user) {
      setDetail(t('authRequired'));
      return;
    }
    if (!form.acceptEcommerce || !form.acceptTrading) {
      setDetail(t('acceptRequired'));
      return;
    }
    const parsed = bazaarCreateSchema.safeParse(form);
    if (!parsed.success) {
      const nextErrors: Record<string, string> = {};
      for (const issue of parsed.error.issues) {
        const field = String(issue.path[0] ?? 'form');
        if (!nextErrors[field]) nextErrors[field] = t('invalidField');
      }
      setErrors(nextErrors);
      return;
    }
    setErrors({});
    setDetail('');
    setSubmitting(true);
    const result = await createBazaar(parsed.data);
    setSubmitting(false);
    if (!result.ok) {
      setDetail(result.error);
      return;
    }
    setCreatedId(result.data.marketplace_id);
  };

  if (createdId) {
    return (
      <Card density="cozy" className="text-center">
        <h2 className="text-xl font-semibold text-ink">{t('successTitle')}</h2>
        <p className="mt-2 text-sm text-ink-soft">{t('successDescription')}</p>
        <p className="num mt-3 font-mono text-sm text-forest">{createdId}</p>
        <div className="mt-5 flex flex-wrap justify-center gap-3">
          <Link
            href={`/${locale}/market/bazaars/${createdId}`}
            className="rounded-md bg-action px-4 py-2 text-sm font-semibold text-on-action"
          >
            {t('viewCreated')}
          </Link>
          <Link
            href={`/${locale}/market/bazaars`}
            className="rounded-md border border-line px-4 py-2 text-sm"
          >
            {t('back')}
          </Link>
        </div>
      </Card>
    );
  }

  const fieldClass =
    'mt-1 w-full rounded-md border border-line bg-surface px-3 py-2 text-ink focus-visible:ring-2 focus-visible:ring-focus';

  return (
    <Card density="cozy">
      {authLoading ? (
        <p className="text-sm text-ink-soft">{t('loadingSession')}</p>
      ) : !user ? (
        <div className="text-center">
          <p className="text-sm text-ink-soft">{t('authRequired')}</p>
          <Link
            href={`/${locale}/auth/login`}
            className="mt-4 inline-block rounded-md bg-action px-4 py-2 text-sm font-semibold text-on-action"
          >
            {t('signIn')}
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} noValidate className="space-y-5">
          {detail ? (
            <p role="alert" className="rounded-md bg-clay/10 p-3 text-sm text-clay">
              {detail}
            </p>
          ) : null}

          <div>
            <label htmlFor="bazaar-name" className="text-sm font-medium text-ink">
              {t('name')}
            </label>
            <input
              id="bazaar-name"
              value={form.name}
              onChange={(event) => update('name', event.target.value)}
              aria-invalid={Boolean(errors.name)}
              aria-describedby={errors.name ? 'bazaar-name-error' : undefined}
              className={fieldClass}
            />
            {errors.name ? (
              <p id="bazaar-name-error" className="mt-1 text-xs text-clay">
                {errors.name}
              </p>
            ) : null}
          </div>

          <div>
            <label htmlFor="bazaar-type" className="text-sm font-medium text-ink">
              {t('type')}
            </label>
            <select
              id="bazaar-type"
              value={form.marketplaceType}
              onChange={(event) =>
                update(
                  'marketplaceType',
                  event.target.value as BazaarCreateInput['marketplaceType'],
                )
              }
              className={fieldClass}
            >
              <option value="cooperative">{t('types.cooperative')}</option>
              <option value="individual">{t('types.individual')}</option>
              <option value="farmers_market">{t('types.farmersMarket')}</option>
              <option value="mixed">{t('types.mixed')}</option>
              <option value="other">{t('types.other')}</option>
            </select>
          </div>

          <div>
            <label htmlFor="bazaar-description" className="text-sm font-medium text-ink">
              {t('description')}
            </label>
            <textarea
              id="bazaar-description"
              value={form.description}
              onChange={(event) => update('description', event.target.value)}
              aria-invalid={Boolean(errors.description)}
              className={`${fieldClass} min-h-28`}
            />
            {errors.description ? (
              <p className="mt-1 text-xs text-clay">{errors.description}</p>
            ) : null}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label htmlFor="bazaar-address" className="text-sm font-medium text-ink">
                {t('address')}
              </label>
              <input
                id="bazaar-address"
                value={form.address}
                onChange={(event) => update('address', event.target.value)}
                aria-invalid={Boolean(errors.address)}
                className={fieldClass}
              />
              {errors.address ? <p className="mt-1 text-xs text-clay">{errors.address}</p> : null}
            </div>
            <div>
              <label htmlFor="bazaar-location" className="text-sm font-medium text-ink">
                {t('location')}
              </label>
              <input
                id="bazaar-location"
                value={form.location}
                onChange={(event) => update('location', event.target.value)}
                aria-invalid={Boolean(errors.location)}
                className={fieldClass}
              />
              {errors.location ? <p className="mt-1 text-xs text-clay">{errors.location}</p> : null}
            </div>
          </div>

          <div>
            <label htmlFor="bazaar-village" className="text-sm font-medium text-ink">
              {t('villageId')}
            </label>
            <input
              id="bazaar-village"
              value={form.villageId}
              onChange={(event) => update('villageId', event.target.value)}
              aria-invalid={Boolean(errors.villageId)}
              className={`${fieldClass} font-mono`}
            />
            {errors.villageId ? <p className="mt-1 text-xs text-clay">{errors.villageId}</p> : null}
          </div>

          <div>
            <label htmlFor="bazaar-rules" className="text-sm font-medium text-ink">
              {t('rulesDocument')}
            </label>
            <textarea
              id="bazaar-rules"
              value={form.rulesDocument}
              onChange={(event) => update('rulesDocument', event.target.value)}
              aria-invalid={Boolean(errors.rulesDocument)}
              className={`${fieldClass} min-h-28`}
            />
            {errors.rulesDocument ? (
              <p className="mt-1 text-xs text-clay">{errors.rulesDocument}</p>
            ) : null}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label htmlFor="bazaar-email" className="text-sm font-medium text-ink">
                {t('contactEmail')}
              </label>
              <input
                id="bazaar-email"
                type="email"
                value={form.contactEmail}
                onChange={(event) => update('contactEmail', event.target.value)}
                aria-invalid={Boolean(errors.contactEmail)}
                className={fieldClass}
              />
              {errors.contactEmail ? (
                <p className="mt-1 text-xs text-clay">{errors.contactEmail}</p>
              ) : null}
            </div>
            <div>
              <label htmlFor="bazaar-phone" className="text-sm font-medium text-ink">
                {t('contactPhone')}
              </label>
              <input
                id="bazaar-phone"
                value={form.contactPhone}
                onChange={(event) => update('contactPhone', event.target.value)}
                aria-invalid={Boolean(errors.contactPhone)}
                className={fieldClass}
              />
              {errors.contactPhone ? (
                <p className="mt-1 text-xs text-clay">{errors.contactPhone}</p>
              ) : null}
            </div>
          </div>

          <div className="space-y-3 rounded-md border border-line p-4">
            <label className="flex items-start gap-3 text-sm text-ink">
              <input
                type="checkbox"
                checked={form.acceptEcommerce}
                onChange={(event) => update('acceptEcommerce', event.target.checked)}
                className="mt-1"
              />
              <span>{t('acceptEcommerce')}</span>
            </label>
            <label className="flex items-start gap-3 text-sm text-ink">
              <input
                type="checkbox"
                checked={form.acceptTrading}
                onChange={(event) => update('acceptTrading', event.target.checked)}
                className="mt-1"
              />
              <span>{t('acceptTrading')}</span>
            </label>
          </div>

          <Button type="submit" variant="primary" loading={submitting} className="w-full">
            {t('submit')}
          </Button>
        </form>
      )}
    </Card>
  );
}
