import { useLang } from '../../i18n/LanguageContext';

interface EmptyStateProps {
  title?: string;
  description?: string;
  action?: { label: string; onClick?: () => void; href?: string };
}

export default function EmptyState({
  title,
  description,
  action,
}: EmptyStateProps) {
  const { lang } = useLang();

  const defaultTitle = lang === 'fa' ? 'هیچ موردی یافت نشد' : 'No items found';
  const defaultDesc = lang === 'fa'
    ? 'با تغییر فیلترها یا اضافه کردن محتوا، نتایج نمایش داده می‌شوند.'
    : 'Try adjusting filters or add content to see results.';

  return (
    <div className="flex flex-col items-center gap-4 rounded-3xl glass p-10 text-center" role="status">
      <span className="text-4xl" aria-hidden>📭</span>
      <h3 className="text-lg font-extrabold text-[var(--color-night-100)]">
        {title ?? defaultTitle}
      </h3>
      <p className="max-w-sm text-sm leading-6 text-[var(--color-night-200)]/60">
        {description ?? defaultDesc}
      </p>
      {action ? (
        action.href ? (
          <a
            href={action.href}
            className="inline-flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-5 py-2.5 text-xs font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03]"
          >
            {action.label}
          </a>
        ) : (
          <button
            type="button"
            onClick={action.onClick}
            className="inline-flex items-center gap-2 rounded-full bg-[var(--color-leaf-500)] px-5 py-2.5 text-xs font-extrabold text-[var(--color-night-950)] transition-transform hover:scale-[1.03]"
          >
            {action.label}
          </button>
        )
      ) : null}
    </div>
  );
}
