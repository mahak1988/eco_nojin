import { useState, type FormEvent } from 'react';
import { CheckCircle2, Send } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { submitPilotApplication, validatePilot } from '../lib/api';
import { pilotIran } from '../content/pages/pilotacademia';

/** Pilot (Iran) landing page — interest form → POST /api/v1/pilot/apply. */
export default function PilotIranPage() {
  const { lang, t } = useLang();
  const c = pilotIran[lang as 'fa' | 'en'];

  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [province, setProvince] = useState('');
  const [hectares, setHectares] = useState('');
  const [crop, setCrop] = useState('');
  const [channel, setChannel] = useState(c.channels[0]);
  const [consent, setConsent] = useState(false);
  const [status, setStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const payload = {
      name,
      phone,
      province,
      land_hectares: hectares ? Number(hectares) : null,
      main_crop: crop || null,
      preferred_channel: channel,
      consent,
      locale: lang,
    };
    if (!validatePilot(payload)) {
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
    'w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:border-[var(--color-leaf-400)]/60 focus:outline-none';

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/pilot-iran" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6" id="offer">
        <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-2">
          <Reveal>
            <div className="glass h-full rounded-3xl p-7">
              <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{c.offerTitle}</h2>
              <ul className="mt-4 flex flex-col gap-3">
                {c.offer.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm leading-7 text-[var(--color-night-200)]/70">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-leaf-400)]" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
          <Reveal delay={0.08}>
            <div className="glass h-full rounded-3xl p-7">
              <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">{c.eligibilityTitle}</h2>
              <ul className="mt-4 flex flex-col gap-3">
                {c.eligibility.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm leading-7 text-[var(--color-night-200)]/70">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-aqua-400)]" aria-hidden />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        </div>
      </section>

      <section className="px-4 pb-10 sm:px-6" id="apply">
        <div className="mx-auto max-w-3xl">
          <SectionHeading kicker={c.kicker} title={c.formTitle} lead={c.formNote} />
          {status === 'success' ? (
            <Reveal className="mt-8">
              <div className="glass flex flex-col items-center gap-3 rounded-3xl p-10 text-center">
                <CheckCircle2 className="h-12 w-12 text-[var(--color-leaf-400)]" aria-hidden />
                <h3 className="text-lg font-extrabold text-[var(--color-night-100)]">{c.successTitle}</h3>
                <p className="text-sm leading-7 text-[var(--color-night-200)]/65">{c.successNote}</p>
              </div>
            </Reveal>
          ) : (
            <Reveal className="mt-8">
              <form onSubmit={handleSubmit} noValidate className="glass flex flex-col gap-4 rounded-3xl p-7">
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]/70">{c.nameLabel}</span>
                    <input type="text" value={name} onChange={(e) => setName(e.target.value)} className={inputCls} required />
                  </label>
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]/70">{c.phoneLabel}</span>
                    <input type="tel" dir="ltr" value={phone} onChange={(e) => setPhone(e.target.value)} className={inputCls} required />
                  </label>
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]/70">{c.provinceLabel}</span>
                    <input type="text" value={province} onChange={(e) => setProvince(e.target.value)} className={inputCls} required />
                  </label>
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]/70">{c.hectaresLabel}</span>
                    <input type="number" min="0" step="0.1" dir="ltr" value={hectares} onChange={(e) => setHectares(e.target.value)} className={inputCls} />
                  </label>
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]/70">{c.cropLabel}</span>
                    <input type="text" value={crop} onChange={(e) => setCrop(e.target.value)} className={inputCls} />
                  </label>
                  <label className="flex flex-col gap-1.5">
                    <span className="text-xs font-bold text-[var(--color-night-200)]/70">{c.channelLabel}</span>
                    <select value={channel} onChange={(e) => setChannel(e.target.value)} className={inputCls}>
                      {c.channels.map((option) => (
                        <option key={option} value={option} className="bg-[var(--color-night-900)] text-[var(--color-night-100)]">
                          {option}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>

                <label className="flex items-start gap-3 text-xs leading-6 text-[var(--color-night-200)]/70">
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
            <p className="mt-1 text-xs leading-6 text-[var(--color-night-200)]/55">{c.timelineNote}</p>
          </div>
        </Reveal>
      </section>
    </>
  );
}
