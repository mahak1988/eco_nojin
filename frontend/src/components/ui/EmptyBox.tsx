import { useLang } from '../../i18n/LanguageContext';
import Icon from './Icon';
import type { IconKey } from '../../content/site';
import type { ReactNode } from 'react';

interface EmptyBoxProps {
  icon?: IconKey;
  title?: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export default function EmptyBox({
  icon = 'clipboard',
  title,
  description,
  action,
  className = '',
}: EmptyBoxProps) {
  const { lang } = useLang();

  const defaultTitle = lang === 'fa' ? 'هیچ داده‌ای وجود ندارد' : 'No data yet';
  const defaultDesc = lang === 'fa'
    ? 'هنوز موردی ثبت نشده. پس از تکمیل اقدامات، نتایج اینجا نمایش داده می‌شوند.'
    : 'Nothing recorded yet. Results will appear here once actions are completed.';

  return (
    <div
      className={`glass rounded-2xl p-8 sm:p-10 flex flex-col items-center text-center gap-4 ${className}`}
      role="status"
      aria-label={lang === 'fa' ? 'بدون داده' : 'No data'}
    >
      {icon ? (
        <span
          className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-[var(--color-leaf-500)]/10"
          aria-hidden="true"
        >
          <Icon name={icon} className="h-8 w-8 text-[var(--color-leaf-500)]/60" />
        </span>
      ) : null}
      <h3 className="text-lg font-extrabold text-[var(--color-night-100)]">
        {title ?? defaultTitle}
      </h3>
      <p className="text-sm leading-6 text-[var(--color-night-200)]/60 max-w-md">
        {description ?? defaultDesc}
      </p>
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}
