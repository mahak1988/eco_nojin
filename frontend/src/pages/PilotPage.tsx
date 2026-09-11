import { useState, type FormEvent } from 'react';
import { CheckCircle2, Send, Upload } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { submitPilotApplication, validatePilot, type PilotFilePayload } from '../lib/api';
import { pilotIran } from '../content/pages/pilotacademia';
import BaseCard from '../components/dashboard/BaseCard';

/** Pilot landing page — interest form with optional file upload → POST /api/v1/pilot/apply. */
export default function PilotPage() {
  const { lang, t } = useLang();
  const c = pilotIran[lang as 'fa' | 'en'];

  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [province, setProvince] = useState('');
  const [hectares, setHectares] = useState('');
  const [crop, setCrop] = useState('');
  const [channel, setChannel] = useState(c.channels[0]);
  const [consent, setConsent] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');

  const fileError = file && file.size > 5 * 1024 * 1024;

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const payload: PilotFilePayload = {
      name,
      phone,
      province,
      land_hectares: hectares ? Number(hectares) : null,
      main_crop: crop || null,
      preferred_channel: channel,
      consent,
      locale: lang,
      file,
    };
    if (!validatePilot(payload) || (file && fileError)) {
      setStatus('error');
      return;
    }
    setStatus('sending');
    try {
      await submitPilotApplication(payload);
      setStatus('success');
    } catch (submitError) {
      console.error('Pilot application failed', submitError);
      setStatus('error');
    }
  };

  const inputCls =
    'w-full rounded-xl border border-[var(--color-night-700)] bg-[var(--color-night-900)] px-4 py-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)] focus:border-[var(--color-leaf-400)] focus:outline-none';

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/pilot" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6" id="offer">
        <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-2">
          <Reveal>
            <BaseCard title={c.offerTitle}>
              <ul className="mt-4 flex flex-col gap-3">
                {c.offer.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm leading-7 text-[var(--color-night-200)]">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-leaf-400)]" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </BaseCard>
          </Reveal>
          <Reveal delay={0.08}>
            <BaseCard title={c.eligibilityTitle}>
              <ul className="mt-4 flex flex-col gap-3">
                {c.eligibility.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm leading-7 text-[var(--color-night-200)]">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-aqua-400)]" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </BaseCard>
          </Reveal>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6" id="apply">
        <div className="mx-auto max-w-3xl">
          <SectionHeading kicker={c.kicker} title={c.formTitle} lead={c.formNote} />
          {status === 'success' ? (
            <Reveal className="mt-8">
              <BaseCard title={c.successTitle} icon={<CheckCircle2 className="h-12 w-12 text-[var(--color-leaf-400)]" aria-hidden />}>
                <p className="text-sm leading-7 text-[var(--color-night-200)]">{c.successNote}</p>
              </BaseCard>
            </Reveal>
          ) : (
            <Reveal className="mt-8">
              <form onSubmit={handleSubmit} noValidate className="glass flex flex-col gap-4 rounded-3xl p-7">
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]">{c.nameLabel}</span>
                    <input type="text" value={name} onChange={(e) => setName(e.target.value)} className={inputCls} required />
                  </label>
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]">{c.phoneLabel}</span>
                    <input type="tel" dir="ltr" value={phone} onChange={(e) => setPhone(e.target.value)} className={inputCls} required />
                  </label>
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]">{c.provinceLabel}</span>
                    <input type="text" value={province} onChange={(e) => setProvince(e.target.value)} className={inputCls} required />
                  </label>
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]">{c.hectaresLabel}</span>
                    <input type="number" min="0" step="0.1" dir="ltr" value={hectares} onChange={(e) => setHectares(e.target.value)} className={inputCls} />
                  </label>
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]">{c.cropLabel}</span>
                    <input type="text" value={crop} onChange={(e) => setCrop(e.target.value)} className={inputCls} />
                  </label>
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]">{c.channelLabel}</span>
                    <select value={channel} onChange={(e) => setChannel(e.target.value)} className={inputCls}>
                      {c.channels.map((option) => (
                        <option key={option} value={option} className="bg-[var(--color-night-900)] text-[var(--color-night-100)]">
                          {option}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <label className="flex flex-col gap-1.5">
                  <span className="text-xs font-bold text-[var(--color-night-200)]">{c.fileUploadLabel}</span>
                  <span className="text-[10px] text-[var(--color-night-200)]">{c.fileUploadNote}</span>
                  <div className="flex items-center gap-3 rounded-xl border border-dashed border-[var(--color-night-700)] bg-[var(--color-night-900)] px-4 py-3">
                    <Upload className="h-4 w-4 shrink-0 text-[var(--color-night-200)]" aria-hidden />
                    <input
                      type="file"
                      accept=".pdf,.doc,.docx"
                      onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                      className="text-sm text-[var(--color-night-100)] file:rounded-full file:border-0 file:bg-[var(--color-leaf-500)] file:px-3 file:py-1.5 file:text-xs file:font-bold file:text-[var(--color-leaf-300)]"
                    />
                  </div>
                  {fileError ? (
                    <p role="alert" className="text-[10px] font-bold text-red-300">
                      {lang === 'fa' ? 'حداکثر حجم فایل ۵ مگابایت است.' : 'File exceeds the 5 MB limit.'}
                    </p>
                  ) : null}
                </label>

                <label className="flex items-start gap-3 text-xs leading-6 text-[var(--color-night-200)]">
                  <input
                    type="checkbox"
                    checked={consent}
                    onChange={(e) => setConsent(e.target.checked)}
                    className="mt-0.5 h-4 w-4 accent-leaf-500"
                    required
                  />
                  {c.consentLabel}
                </label>

                {status === 'error' ? (
                  <p role="alert" className="rounded-xl border border-red-400/30 bg-red-400/10 p-3 text-xs font-bold text-red-300">
                    {c.validationError}
                  </p>
                ) : null}

                <button
                  type="submit"
                  disabled={status === 'sending'}
                  className="ring-glow inline-flex items-center justify-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-6 py-3 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.02] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Send className="h-4 w-4" aria-hidden />
                  {status === 'sending' ? '…' : c.submitButton}
                </button>
              </form>
            </Reveal>
          )}
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6" id="timeline">
        <Reveal className="mx-auto max-w-3xl">
          <div className="glass rounded-2xl p-5">
            <p className="text-sm font-extrabold text-[var(--color-night-100)]">{c.timelineTitle}</p>
            <p className="mt-1 text-xs leading-6 text-[var(--color-night-200)]">{c.timelineNote}</p>
          </div>
        </Reveal>
      </section>
    </>
  );
}
