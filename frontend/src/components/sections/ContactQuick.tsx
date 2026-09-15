import { useLang } from '../../i18n/LanguageContext';
import { Mail, Phone, MapPin } from 'lucide-react';

/** Quick contact links section. */
export default function ContactQuick() {
  const { lang } = useLang();

  return (
    <section className="px-4 py-12 sm:px-6" aria-label="Quick contact">
      <div className="mx-auto max-w-4xl">
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="flex items-center gap-3 rounded-2xl glass p-5">
            <Mail className="h-5 w-5 text-[var(--color-leaf-400)]" aria-hidden />
            <div>
              <p className="text-xs text-[var(--color-night-200)]/50">{lang === 'fa' ? 'ایمیل' : 'Email'}</p>
              <p className="text-sm font-bold text-[var(--color-night-100)]">info@econojin.org</p>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-2xl glass p-5">
            <Phone className="h-5 w-5 text-[var(--color-aqua-400)]" aria-hidden />
            <div>
              <p className="text-xs text-[var(--color-night-200)]/50">{lang === 'fa' ? 'تلفن' : 'Phone'}</p>
              <p className="text-sm font-bold text-[var(--color-night-100)]">+98 21 1234 5678</p>
            </div>
          </div>
          <div className="flex items-center gap-3 rounded-2xl glass p-5">
            <MapPin className="h-5 w-5 text-[var(--color-sand-400)]" aria-hidden />
            <div>
              <p className="text-xs text-[var(--color-night-200)]/50">{lang === 'fa' ? 'آدرس' : 'Address'}</p>
              <p className="text-sm font-bold text-[var(--color-night-100)]">تهران، خیابان کوچک</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
