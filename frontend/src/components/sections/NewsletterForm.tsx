import { useState } from 'react';
import { useLang } from '../../i18n/LanguageContext';
import { Mail, CheckCircle2 } from 'lucide-react';
import Reveal from '../ui/Reveal';

/** Newsletter email subscription form. */
export default function NewsletterForm() {
  const { lang } = useLang();
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      setError(lang === 'fa' ? 'لطفاً ایمیل معتبر وارد کنید' : 'Please enter a valid email');
      return;
    }
    setError('');
    setSubmitted(true);
  };

  return (
    <Reveal>
      <section className="px-4 py-16 sm:px-6" aria-label={lang === 'fa' ? 'اشتراک خبرنامه' : 'Newsletter'}>
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-2xl font-extrabold text-[var(--color-night-100)] sm:text-3xl">
            {lang === 'fa' ? 'اخبار را دریافت کنید' : 'Stay Updated'}
          </h2>
          <p className="mt-3 text-[var(--color-night-200)]/60">
            {lang === 'fa'
              ? 'هر هفته آخرین تحقیقات، اخبار و راهکارها را دریافت کنید.'
              : 'Get the latest research, news, and insights every week.'}
          </p>

          {submitted ? (
            <div className="mt-8 flex items-center justify-center gap-2 rounded-3xl glass p-6 text-[var(--color-leaf-400)]">
              <CheckCircle2 className="h-6 w-6" aria-hidden />
              <span className="font-bold">
                {lang === 'fa' ? 'با موفقیت ثبت شد!' : 'Successfully subscribed!'}
              </span>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
              <div className="relative flex-1">
                <Mail className="absolute start-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-night-200)]/40" aria-hidden />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder={lang === 'fa' ? 'ایمیل شما' : 'Your email'}
                  className="w-full rounded-full bg-white/5 border border-white/10 pl-10 pr-4 py-3 text-sm text-[var(--color-night-100)] placeholder:text-[var(--color-night-200)]/30 focus:border-[var(--color-leaf-500)] focus:outline-none"
                  aria-label={lang === 'fa' ? 'ایمیل برای اشتراک' : 'Email for subscription'}
                  required
                />
              </div>
              <button
                type="submit"
                className="inline-flex items-center justify-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-7 py-3 text-sm font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03] active:scale-[0.97]"
              >
                {lang === 'fa' ? 'اشتراک' : 'Subscribe'}
              </button>
            </form>
          )}
          {error && <p className="mt-3 text-sm text-red-400">{error}</p>}
        </div>
      </section>
    </Reveal>
  );
}
