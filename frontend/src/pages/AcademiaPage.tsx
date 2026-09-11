import { useState, type FormEvent } from 'react';
import { CheckCircle2, Send } from 'lucide-react';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import SectionHeading from '../components/ui/SectionHeading';
import { useLang } from '../i18n/LanguageContext';
import { submitContact } from '../lib/contact';
import { academia } from '../content/pages/pilotacademia';

/** Academia landing — research collaboration form reusing the contact API. */
export default function AcademiaPage() {
  const { lang, t } = useLang();
  const c = academia[lang as 'fa' | 'en'];

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [affiliation, setAffiliation] = useState('');
  const [topic, setTopic] = useState('');
  const [status, setStatus] = useState<'idle' | 'sending' | 'success' | 'error'>('idle');

  const emailValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (name.trim().length < 2 || !emailValid || affiliation.trim().length < 2 || topic.trim().length < 10) {
      setStatus('error');
      return;
    }
    setStatus('sending');
    try {
      await submitContact({
        name,
        email,
        role: lang === 'fa' ? 'پژوهشگر' : 'Researcher',
        message: `${c.affiliationLabel}: ${affiliation}\n${c.topicLabel}: ${topic}`,
        locale: lang,
      });
      setStatus('success');
    } catch (submitError) {
      console.error('Academia request failed', submitError);
      setStatus('error');
    }
  };

  const inputCls =
    'w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:border-[var(--color-leaf-400)]/60 focus:outline-none';

  return (
    <>
      <Seo title={`${c.title} | ${t.brand.name}`} description={c.lead} path="/academia" />
      <PageHeader kicker={c.kicker} title={c.title} lead={c.lead} />

      <section className="px-4 py-10 sm:px-6" id="models">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <SectionHeading kicker={c.kicker} title={c.modelsTitle} />
          <div className="grid gap-4 lg:grid-cols-3">
            {c.models.map((model, index) => (
              <Reveal key={model.title} delay={index * 0.07}>
                <div className="glass glass-hover h-full rounded-3xl p-6">
                  <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{model.title}</h3>
                  <p className="mt-2 text-sm leading-7 text-[var(--color-night-200)]/60">{model.desc}</p>
                </div>
              </Reveal>
            ))}
          </div>
          <Reveal>
            <div className="glass rounded-3xl p-7">
              <h2 className="text-base font-extrabold text-[var(--color-night-100)]">{c.provideTitle}</h2>
              <ul className="mt-3 flex flex-col gap-2.5">
                {c.provide.map((item) => (
                  <li key={item} className="flex items-start gap-3 text-sm leading-7 text-[var(--color-night-200)]/65">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-leaf-400)]" aria-hidden />
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
                    <span className="text-xs font-bold text-[var(--color-night-200)]/70">{c.emailLabel}</span>
                    <input type="email" dir="ltr" value={email} onChange={(e) => setEmail(e.target.value)} className={inputCls} required />
                  </label>
                </div>
                <label className="flex flex-col gap-1.5">
                  <span className="text-xs font-bold text-[var(--color-night-200)]/70">{c.affiliationLabel}</span>
                  <input type="text" value={affiliation} onChange={(e) => setAffiliation(e.target.value)} className={inputCls} required />
                </label>
                <label className="flex flex-col gap-1.5">
                  <span className="text-xs font-bold text-[var(--color-night-200)]/70">{c.topicLabel}</span>
                  <textarea value={topic} onChange={(e) => setTopic(e.target.value)} rows={4} className={inputCls} required />
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
    </>
  );
}
