import { Link } from '@tanstack/react-router';
import { useTranslation } from 'react-i18next';
import { Button, EmptyState } from '@eco/ui';

export function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <EmptyState
      title={t('notFound.title', '۴۰۴ — صفحه پیدا نشد')}
      description={t('notFound.body', 'صفحه‌ای که دنبالش بودید جابه‌جا شده یا هرگز وجود نداشته است.')}
      action={
        <Link
          to="/"
          className="inline-flex items-center justify-center rounded-md bg-brand-600 px-6 py-2 text-sm font-medium text-white"
        >
          {t('notFound.goHome', 'بازگشت به خانه')}
        </Link>
      }
    />
  );
}
