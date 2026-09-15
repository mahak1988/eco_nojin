import { useLang } from '../../i18n/LanguageContext';
import { NewsItem } from '../../data/homeData';

/** Social media feed embed style card. */
export default function SocialFeedEmbed({
  items,
}: {
  items?: NewsItem[];
}) {
  const { lang } = useLang();
  const data = items || [];

  if (data.length === 0) {
    return (
      <div className="rounded-3xl glass p-6 text-center">
        <p className="text-sm text-[var(--color-night-200)]/50">
          {lang === 'fa' ? 'فید اجتماعی در حال بارگذاری...' : 'Loading social feed...'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {data.map((item, i) => (
        <div key={i} className="flex items-start gap-3 rounded-2xl glass p-4 hover:bg-white/[0.06] transition-colors">
          <div className="flex flex-col items-center">
            <span className="w-8 h-8 rounded-full bg-[var(--color-leaf-500)]/15 flex items-center justify-center text-sm">📰</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-[var(--color-night-200)]/60">
                {item.category}
              </span>
              <span className="text-[10px] text-[var(--color-night-200)]/40">{item.date}</span>
            </div>
            <p className="text-xs font-bold text-[var(--color-night-100)]">{item.title}</p>
            <p className="text-[10px] text-[var(--color-night-200)]/50 mt-0.5 line-clamp-2">{item.excerpt}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
