import { useLang } from '../../i18n/LanguageContext';
import { Twitter, Linkedin, Youtube, Instagram, Send } from 'lucide-react';

/** Social media links bar. */
export default function SocialBar() {
  const { lang } = useLang();

  const socials = [
    { icon: Twitter, label: 'Twitter', url: 'https://twitter.com' },
    { icon: Linkedin, label: 'LinkedIn', url: 'https://linkedin.com' },
    { icon: Youtube, label: 'YouTube', url: 'https://youtube.com' },
    { icon: Instagram, label: 'Instagram', url: 'https://instagram.com' },
    { icon: Send, label: 'Telegram', url: 'https://t.me' },
  ];

  return (
    <section className="px-4 py-8 sm:px-6" aria-label="Social media">
      <div className="mx-auto max-w-6xl flex flex-col items-center gap-4">
        <p className="text-xs text-[var(--color-night-200)]/40">
          {lang === 'fa' ? 'ما را دنبال کنید' : 'Follow Us'}
        </p>
        <div className="flex gap-3">
          {socials.map(({ icon: Icon, label, url }) => (
            <a
              key={label}
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center h-10 w-10 rounded-full glass glass-hover text-[var(--color-night-200)]/60 hover:text-[var(--color-leaf-300)] transition-colors"
              aria-label={label}
            >
              <Icon className="h-4 w-4" aria-hidden />
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
