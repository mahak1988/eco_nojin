'use client';

import { useTranslations } from 'next-intl';
import { useId, useState } from 'react';

/**
 * The USSD / SMS message editor.
 *
 * The character limit is not a style preference here. It is the difference
 * between a message that arrives and one that is silently dropped, and the
 * inclusive-access requirement this page exists to serve is precisely that a
 * reader on a feature phone can use the platform at all. A reader who cannot
 * see, in advance, that their message will be split is a reader who finds out
 * from the fact that nothing arrived.
 *
 * So the limit sits next to the field at all times rather than appearing only
 * after it is crossed, and the segment count starts at zero rather than after
 * the first keystroke: a constraint that is invisible until it bites has already
 * failed the person it constrains.
 *
 * No network call is made from here. The gateway's own menu preview is rendered
 * by the server component above, so the text a reader compares against is the
 * text the gateway actually produced rather than a sample.
 */

/** GSM 07.05: one SMS segment carries 160 characters. */
const SMS_SEGMENT = 160;
/** A USSD display string is capped at 182 characters across the session. */
const USSD_LIMIT = 182;
/** The handset concatenates at most 20 segments into one message. */
const MAX_SEGMENTS = 20;

type Verdict = 'idle' | 'within' | 'split' | 'over';

function segmentsFor(count: number, limit: number): number {
  return count === 0 ? 0 : Math.ceil(count / limit);
}

function verdictFor(count: number, limit: number, channel: 'ussd' | 'sms'): Verdict {
  if (count === 0) return 'idle';
  if (channel === 'ussd') return count > limit ? 'over' : 'within';
  const segments = Math.ceil(count / limit);
  if (segments > MAX_SEGMENTS) return 'over';
  return segments > 1 ? 'split' : 'within';
}

function ChannelField({
  id,
  label,
  limit,
  channel,
  value,
  onChange,
}: {
  id: string;
  label: string;
  limit: number;
  channel: 'ussd' | 'sms';
  value: string;
  onChange: (next: string) => void;
}) {
  const t = useTranslations('public.telecom');
  const count = value.length;
  const segments = segmentsFor(count, limit);
  const verdict = verdictFor(count, limit, channel);
  const over = verdict === 'over';

  return (
    <div className="min-w-0">
      <label htmlFor={id} className="field-label block">
        {label}
      </label>
      <div className="mt-2 flex flex-wrap items-baseline justify-between gap-2">
        <span className="num text-xs text-ink-soft">
          {channel === 'ussd' ? t('editorLimitUssd') : t('editorLimitSms')}: {limit}
        </span>
        <span
          className={`num text-xs ${over ? 'text-clay' : 'text-ink-soft'}`}
          aria-live="polite"
          data-verdict={verdict}
        >
          {count}/{limit}
        </span>
      </div>
      <textarea
        id={id}
        value={value}
        rows={3}
        dir="auto"
        onChange={(event) => onChange(event.target.value)}
        className="mt-2 w-full rounded-[var(--radius-8)] border border-line bg-surface p-3 text-sm text-ink"
      />
      <p className="mt-1 text-xs text-ink-soft">
        {t('editorSegments')}: {segments} ·{' '}
        {verdict === 'over' || verdict === 'split'
          ? t('editorOver')
          : verdict === 'within'
            ? t('editorWithin')
            : '—'}
      </p>
    </div>
  );
}

export function MessageEditor() {
  const t = useTranslations('public.telecom');
  const ussdId = useId();
  const smsId = useId();
  const [ussd, setUssd] = useState('');
  const [sms, setSms] = useState('');

  return (
    <div className="grid gap-5">
      <p className="text-sm text-ink-soft">{t('editorLead')}</p>
      <p className="text-xs text-ink-soft">{t('editorRule')}</p>
      <ChannelField
        id={ussdId}
        label={t('editorUssd')}
        limit={USSD_LIMIT}
        channel="ussd"
        value={ussd}
        onChange={setUssd}
      />
      <p className="text-xs text-ink-soft">{t('editorUssdNote')}</p>
      <ChannelField
        id={smsId}
        label={t('editorSms')}
        limit={SMS_SEGMENT}
        channel="sms"
        value={sms}
        onChange={setSms}
      />
    </div>
  );
}
