import { useLang } from '../../i18n/LanguageContext';
import { Facebook, Twitter, Linkedin, Link2 } from 'lucide-react';

/** Share page on social media. */
export default function ShareWidget() {
  const { lang } = useLang();

  const share = (platform: string) => {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(lang === 'fa' ? 'پلتفرم Eco Nojin' : 'Eco Nojin Platform');
    const urls: Record<string, string> = {
      twitter: `https://twitter.com/intent/tweet?url=${url}&text=${text}`,
      facebook: `https://www.facebook.com/sharer/sharer.php?u=${url}`,
      linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${url}`,
      copy: '',
    };
    if (platform === 'copy') {
      navigator.clipboard?.writeText(window.location.href);
      return;
    }
    window.open(urls[platform], '_blank', 'width=600,height=400');
  };

  const platforms = [
    { key: 'twitter', icon: Twitter, label: 'X' },
    { key: 'facebook', icon: Facebook, label: 'FB' },
    { key: 'linkedin', icon: Linkedin, label: 'LI' },
    { key: 'copy', icon: Link2, label: '🔗' },
  ];

  return (
    <div className="flex gap-2">
      {platforms.map(({ key, icon: Icon, label }) => (
        <button
          key={key}
          type="button"
          onClick={() => share(key)}
          className="rounded-xl glass p-2 text-[var(--color-night-200)]/40 hover:text-[var(--color-leaf-300)] transition-colors"
          aria-label={label}
          title={label}
        >
          <Icon className="h-4 w-4" aria-hidden />
        </button>
      ))}
    </div>
  );
}
