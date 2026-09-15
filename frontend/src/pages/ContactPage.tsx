import { useState, type FormEvent } from 'react';
import { CheckCircle2, Mail, MessageSquare, Send, TriangleAlert } from 'lucide-react';
import { Link } from 'react-router-dom';
import Seo from '../components/ui/Seo';
import PageHeader from '../components/sections/PageHeader';
import Reveal from '../components/ui/Reveal';
import { useLang } from '../i18n/LanguageContext';
import {
  buildContactMailto,
  submitContact,
  validateContact,
  type ContactFieldError,
} from '../lib/contact';

const CONTACT_EMAIL = 'info@econojin.org';

type Status = 'idle' | 'sending' | 'success' | 'error';

/** Contact page — posts to the gateway contact API; mailto fallback on failure. */
export default function ContactPage() {
  const { t, lang } = useLang();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [role, setRole] = useState(t.contact.roles[0]);
  const [message, setMessage] = useState('');
  const [website, setWebsite] = useState(''); // honeypot
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState<string | null>(null);
  const [invalidField, setInvalidField] = useState<ContactFieldError | null>(null);

  const payload = { name, email, role, message, locale: lang, website };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const fieldError = validateContact(payload);
    if (fieldError) {
      setInvalidField(fieldError);
      setError(t.contact.validationError);
      return;
    }
    setInvalidField(null);
    setError(null);
    setStatus('sending');
    try {
      await submitContact(payload);
      setStatus('success');
    } catch (submitError) {
      console.error('Contact submission failed', submitError);
      setStatus('error');
    }
  };

  const resetForm = () => {
    setName('');
    setEmail('');
    setRole(t.contact.roles[0]);
    setMessage('');
    setWebsite('');
    setStatus('idle');
    setError(null);
    setInvalidField(null);
  };

  const inputCls = (invalid: boolean) =>
    `w-full rounded-xl border bg-white/5 px-4 py-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:outline-none ${
      invalid ? 'border-red-400/60' : 'border-white/10 focus:border-[var(--color-leaf-400)]/60'
    }`;

  return (
    <>
      <Seo
        title={`${t.contact.title} | ${t.brand.name}`}
        description={t.contact.lead}
        path="/contact"
      />
      <PageHeader kicker={t.contact.kicker} title={t.contact.title} lead={t.contact.lead} />

      <section className="px-4 py-10 sm:px-6">
        <div className="mx-auto grid max-w-4xl gap-6 lg:grid-cols-[1.2fr_1fr]">
          {/* form / status */}
          <Reveal>
            {status === 'success' ? (
              <div className="glass flex flex-col items-start gap-3 rounded-3xl p-8">
                <CheckCircle2 className="h-10 w-10 text-[var(--color-leaf-400)]" aria-hidden />
                <h2 className="text-lg font-extrabold text-[var(--color-night-100)]">
                  {t.contact.successTitle}
                </h2>
                <p className="text-sm leading-7 text-[var(--color-night-200)]/65">{t.contact.successNote}</p>
                <button
                  type="button"
                  onClick={resetForm}
                  className="mt-2 rounded-full bg-[var(--color-leaf-500)]/15 px-5 py-2 text-xs font-extrabold text-[var(--color-leaf-300)] hover:bg-[var(--color-leaf-500)]/25"
                >
                  {t.contact.formTitle}
                </button>
              </div>
            ) : (
              <form
                onSubmit={handleSubmit}
                noValidate
                className="glass flex flex-col gap-4 rounded-3xl p-7"
                aria-labelledby="contact-form-title"
              >
                <h2 id="contact-form-title" className="text-lg font-extrabold text-[var(--color-night-100)]">
                  {t.contact.formTitle}
                </h2>
                <p className="text-xs leading-6 text-[var(--color-night-200)]/50">{t.contact.formNote}</p>
              <p className="text-xs leading-6 text-[var(--color-night-200)]/50">
                <Link to="/faq" className="font-bold text-[var(--color-leaf-300)] hover:underline">
                  {t.contact.faqLink}
                </Link>
              </p>

                <label className="flex flex-col gap-1.5">
                  <span className="text-xs font-bold text-[var(--color-night-200)]/70">
                    {t.contact.nameLabel}
                  </span>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className={inputCls(invalidField === 'name')}
                    required
                  />
                </label>

                <label className="flex flex-col gap-1.5">
                  <span className="text-xs font-bold text-[var(--color-night-200)]/70">
                    {t.contact.emailLabel}
                  </span>
                  <input
                    type="email"
                    dir="ltr"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={inputCls(invalidField === 'email')}
                    required
                  />
                </label>

                <label className="flex flex-col gap-1.5">
                  <span className="text-xs font-bold text-[var(--color-night-200)]/70">
                    {t.contact.roleLabel}
                  </span>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className={inputCls(false)}
                  >
                    {t.contact.roles.map((option) => (
                      <option key={option} value={option} className="bg-[var(--color-night-900)] text-[var(--color-night-100)]">
                        {option}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="flex flex-col gap-1.5">
                  <span className="text-xs font-bold text-[var(--color-night-200)]/70">
                    {t.contact.messageLabel}
                  </span>
                  <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    rows={5}
                    className={inputCls(invalidField === 'message')}
                    required
                  />
                </label>

                {/* honeypot — hidden from real users */}
                <div aria-hidden className="absolute start-[-9999px]">
                  <label>
                    Website
                    <input
                      type="text"
                      tabIndex={-1}
                      autoComplete="off"
                      value={website}
                      onChange={(e) => setWebsite(e.target.value)}
                    />
                  </label>
                </div>

                {status === 'idle' && error ? (
                  <p role="alert" className="rounded-xl border border-red-400/30 bg-red-400/10 p-3 text-xs font-bold text-red-300">
                    {error}
                  </p>
                ) : null}

                {status === 'error' ? (
                  <div
                    role="alert"
                    className="flex flex-col gap-3 rounded-xl border border-red-400/30 bg-red-400/10 p-4"
                  >
                    <span className="flex items-center gap-2 text-xs font-bold text-red-300">
                      <TriangleAlert className="h-4 w-4" aria-hidden />
                      {t.contact.errorTitle}
                    </span>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        onClick={() => setStatus('idle')}
                        className="rounded-full bg-white/10 px-4 py-2 text-xs font-bold text-[var(--color-night-100)] hover:bg-white/15"
                      >
                        {lang === 'fa' ? 'تلاش دوباره' : 'Retry'}
                      </button>
                      <a
                        href={buildContactMailto(payload, CONTACT_EMAIL)}
                        className="rounded-full bg-[var(--color-leaf-500)]/15 px-4 py-2 text-xs font-bold text-[var(--color-leaf-300)] hover:bg-[var(--color-leaf-500)]/25"
                      >
                        {t.contact.errorFallback}
                      </a>
                    </div>
                  </div>
                ) : null}

                <button
                  type="submit"
                  disabled={status === 'sending'}
                  className="ring-glow inline-flex items-center justify-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-6 py-3 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Send className="h-4 w-4" aria-hidden />
                  {status === 'sending' ? '…' : t.contact.sendButton}
                </button>
              </form>
            )}
          </Reveal>

          {/* side cards */}
          <div className="flex flex-col gap-5">
            <Reveal delay={0.08}>
              <div className="glass flex flex-col gap-2 rounded-3xl p-7">
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--color-leaf-500)]/12 text-[var(--color-leaf-300)]">
                  <Mail className="h-5 w-5" aria-hidden />
                </span>
                <h2 className="mt-2 text-sm font-extrabold text-[var(--color-night-100)]">
                  {t.contact.emailCardTitle}
                </h2>
                <a
                  href={`mailto:${CONTACT_EMAIL}`}
                  dir="ltr"
                  className="text-sm font-bold text-[var(--color-leaf-300)] hover:underline"
                >
                  {CONTACT_EMAIL}
                </a>
              </div>
            </Reveal>

            <Reveal delay={0.16}>
              <div className="glass flex flex-col gap-2 rounded-3xl p-7">
                <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--color-aqua-500)]/12 text-[var(--color-aqua-300)]">
                  <MessageSquare className="h-5 w-5" aria-hidden />
                </span>
                <h2 className="mt-2 text-sm font-extrabold text-[var(--color-night-100)]">
                  {t.contact.channelsTitle}
                </h2>
                <p className="text-xs leading-6 text-[var(--color-night-200)]/55">
                  {t.contact.channelsNote}
                </p>
              </div>
            </Reveal>
          </div>
        </div>
      </section>

      <p className="pb-6 text-center text-xs text-[var(--color-night-200)]/35" dir={lang === 'fa' ? 'rtl' : 'ltr'}>
        {lang === 'fa'
          ? 'پیام شما فقط با نام، ایمیل، نقش و متن پیام ذخیره می‌شود؛ بدون IP و بدون ردیاب.'
          : 'Only your name, email, role and message are stored — no IP, no trackers.'}
      </p>
    </>
  );
}
