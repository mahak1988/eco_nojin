'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { type FormEvent, useState } from 'react';

import { useAuth } from '@/components/providers/AuthProvider';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { apiPost } from '@/lib/api/client';

/** `POST /api/v1/marketplace/villages/b2b/demands` — `services/api_gateway/routers/village_hub.py`. */
const DEMANDS_SOURCE = '/api/v1/marketplace/villages/b2b/demands';

const EMPTY = { commodity: '', quantity: '', unit: '', frequency: 'monthly' };

/**
 * Field limits, copied from `B2BDemandCreate` in
 * `services/marketplace/schemas/hub_schemas.py:453`.
 *
 * The client repeats the server's bounds so a value the gateway would reject with
 * a 400 is caught before the request; it does not replace them. The server is the
 * authority and re-validates every field.
 */
function validate(form: typeof EMPTY): Record<string, string> {
  const errors: Record<string, string> = {};
  const commodity = form.commodity.trim();
  if (commodity.length < 2 || commodity.length > 100) errors.commodity = 'commodity';
  const quantity = Number(form.quantity.trim());
  if (form.quantity.trim() === '' || !Number.isFinite(quantity) || quantity <= 0) {
    errors.quantity = 'quantity';
  }
  const unit = form.unit.trim();
  if (unit.length < 1 || unit.length > 50) errors.unit = 'unit';
  if (form.frequency.trim().length > 30) errors.frequency = 'frequency';
  return errors;
}

/**
 * The B2B demand form.
 *
 * Two rules from the master plan decide what this form is allowed to ask for.
 *
 * "A shop has no marketplace" and "minimal personal data": the handler derives
 * `buyer_id` from the session (`create_b2b_demand(payload…, user.id)`) and
 * `B2BDemandCreate.buyer_name` is optional, so the form does not collect a name
 * at all. A demand created here carries no personal data the gateway did not
 * already hold.
 *
 * "A unique key": the contract accepts no idempotency key, so the form does not
 * pretend to have one. It never auto-retries, and the submit control is disabled
 * while a request is in flight, so a duplicate is only ever a deliberate second
 * press rather than a silent replay.
 */
export function DemandForm() {
  const t = useTranslations('market.demand');
  const form_t = useTranslations('market.form');
  const pathname = usePathname();
  const locale = pathname.split('/')[1] || 'fa';
  const { user, loading: authLoading } = useAuth();

  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [detail, setDetail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [createdId, setCreatedId] = useState('');

  const update = (key: keyof typeof EMPTY, value: string) => {
    setForm((current) => ({ ...current, [key]: value }));
    setErrors((current) => ({ ...current, [key]: '' }));
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (authLoading || submitting) return;
    if (!user) {
      setDetail(form_t('authRequired'));
      return;
    }
    const found = validate(form);
    setErrors(found);
    if (Object.keys(found).length > 0) {
      setDetail(form_t('invalidField'));
      return;
    }
    setDetail('');
    setSubmitting(true);
    const result = await apiPost<{ id?: string }>(DEMANDS_SOURCE, {
      commodity: form.commodity.trim(),
      // Sent as the typed string, not as a JSON number: the contract declares
      // `Decimal`, and a float would hand the gateway a binary approximation of
      // a quantity before pydantic ever sees it.
      quantity_required: form.quantity.trim(),
      unit: form.unit.trim(),
      frequency: form.frequency.trim() || 'monthly',
    });
    setSubmitting(false);
    if (!result.ok) {
      setDetail(result.error);
      return;
    }
    setCreatedId(String(result.data?.id ?? ''));
  };

  if (createdId) {
    return (
      <Card density="cozy" className="text-center">
        <h2 className="text-xl font-semibold text-ink">{t('createdTitle')}</h2>
        <p className="mt-2 text-sm text-ink-soft">{t('createdDescription')}</p>
        {createdId ? <p className="num mt-3 font-mono text-sm text-forest">{createdId}</p> : null}
        <div className="mt-5 flex flex-wrap justify-center gap-3">
          <Link
            href={`/${locale}/market/villages/b2b/demands/my`}
            className="rounded-md border border-[var(--line)] px-4 py-2 text-sm"
          >
            {t('yourDemands')}
          </Link>
        </div>
      </Card>
    );
  }

  const field =
    'mt-1 w-full rounded-md border border-[var(--line)] bg-surface px-3 py-2 text-ink focus-visible:ring-2 focus-visible:ring-focus';

  return (
    <Card density="cozy">
      {authLoading ? (
        <p className="text-sm text-ink-soft">{form_t('loadingSession')}</p>
      ) : !user ? (
        <div className="text-center">
          <p className="text-sm text-ink-soft">{form_t('authRequired')}</p>
          <Link
            href={`/${locale}/auth/login`}
            className="mt-4 inline-block rounded-md bg-action px-4 py-2 text-sm font-semibold text-on-action"
          >
            {form_t('signIn')}
          </Link>
        </div>
      ) : (
        <form onSubmit={handleSubmit} noValidate className="space-y-5">
          {detail ? (
            <p role="alert" className="rounded-md bg-clay/10 p-3 text-sm text-clay">
              {detail}
            </p>
          ) : null}
          <p className="text-xs text-ink-soft">{form_t('requiredHint')}</p>

          <div>
            <label htmlFor="demand-commodity" className="text-sm font-medium text-ink">
              {t('commodity')}
            </label>
            <input
              id="demand-commodity"
              value={form.commodity}
              onChange={(event) => update('commodity', event.target.value)}
              aria-invalid={Boolean(errors.commodity)}
              aria-describedby={errors.commodity ? 'demand-commodity-error' : undefined}
              className={field}
            />
            {errors.commodity ? (
              <p id="demand-commodity-error" className="mt-1 text-xs text-clay">
                {form_t('invalidField')}
              </p>
            ) : null}
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label htmlFor="demand-quantity" className="text-sm font-medium text-ink">
                {t('quantity')}
              </label>
              <input
                id="demand-quantity"
                inputMode="decimal"
                value={form.quantity}
                onChange={(event) => update('quantity', event.target.value)}
                aria-invalid={Boolean(errors.quantity)}
                className={`${field} num`}
              />
              {errors.quantity ? (
                <p className="mt-1 text-xs text-clay">{form_t('invalidField')}</p>
              ) : null}
            </div>
            <div>
              <label htmlFor="demand-unit" className="text-sm font-medium text-ink">
                {t('unit')}
              </label>
              <input
                id="demand-unit"
                value={form.unit}
                onChange={(event) => update('unit', event.target.value)}
                aria-invalid={Boolean(errors.unit)}
                className={field}
              />
              {errors.unit ? (
                <p className="mt-1 text-xs text-clay">{form_t('invalidField')}</p>
              ) : null}
            </div>
          </div>

          <div>
            <label htmlFor="demand-frequency" className="text-sm font-medium text-ink">
              {t('frequency')}
            </label>
            <input
              id="demand-frequency"
              value={form.frequency}
              onChange={(event) => update('frequency', event.target.value)}
              aria-invalid={Boolean(errors.frequency)}
              className={field}
            />
            {errors.frequency ? (
              <p className="mt-1 text-xs text-clay">{form_t('invalidField')}</p>
            ) : null}
          </div>

          <Button type="submit" variant="primary" loading={submitting} className="w-full">
            {t('submit')}
          </Button>
        </form>
      )}
    </Card>
  );
}
