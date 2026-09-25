'use client';

import { useMessages, useTranslations } from 'next-intl';
import { isMachineTranslated } from './locale-meta';

/** Rendered only when the active catalogue declares itself machine-translated. */
export function MachineTranslationNotice({ className = '' }: { className?: string }) {
  const t = useTranslations('common');
  const machineTranslated = isMachineTranslated(useMessages());

  if (!machineTranslated) return null;

  return <p className={`chip ${className}`.trim()}>{t('machineTranslatedNotice')}</p>;
}
