import { useLang } from '../../i18n/LanguageContext';
import { Smartphone, Tablet, Laptop } from 'lucide-react';
import Reveal from '../ui/Reveal';

/** App download CTA with store badges. */
export default function AppDownload() {
  const { lang } = useLang();

  return (
    <Reveal>
      <section className="px-4 py-16 sm:px-6 lg:py-24" id="app-download" aria-labelledby="app-heading">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mb-4 flex justify-center gap-4">
            <Smartphone className="h-8 w-8 text-[var(--color-leaf-400)]" aria-hidden />
            <Tablet className="h-8 w-8 text-[var(--color-aqua-400)]" aria-hidden />
            <Laptop className="h-8 w-8 text-[var(--color-sand-400)]" aria-hidden />
          </div>
          <h2 id="app-heading" className="text-3xl font-extrabold text-[var(--color-night-100)] sm:text-4xl">
            {lang === 'fa' ? 'اکو نوژین را دانلود کنید' : 'Download Eco Nojin'}
          </h2>
          <p className="mt-3 text-[var(--color-night-200)]/60">
            {lang === 'fa'
              ? 'پنج کانال دسترسی: وب، iOS، Android، Telegram، و USSD.'
              : 'Five access channels: Web, iOS, Android, Telegram, and USSD.'}
          </p>

          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <a href="https://apps.apple.com" target="_blank" rel="noopener noreferrer" className="rounded-full glass glass-hover px-6 py-3 text-sm font-bold text-[var(--color-night-100)]">
              {lang === 'fa' ? 'App Store' : 'App Store'}
            </a>
            <a href="https://play.google.com" target="_blank" rel="noopener noreferrer" className="rounded-full glass glass-hover px-6 py-3 text-sm font-bold text-[var(--color-night-100)]">
              {lang === 'fa' ? 'Google Play' : 'Google Play'}
            </a>
            <a href="https://t.me" target="_blank" rel="noopener noreferrer" className="rounded-full glass glass-hover px-6 py-3 text-sm font-bold text-[var(--color-night-100)]">
              {lang === 'fa' ? 'Telegram' : 'Telegram'}
            </a>
          </div>
        </div>
      </section>
    </Reveal>
  );
}
