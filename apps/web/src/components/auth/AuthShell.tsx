'use client';

import { useLocale } from 'next-intl';
import type { ReactNode } from 'react';
import { SiteNav } from '@/components/SiteNav';
import { MachineTranslationNotice } from './MachineTranslationNotice';

export interface AuthShellProps {
  title: string;
  lead: string;
  children: ReactNode;
  footer?: ReactNode;
}

/** Shared frame for the auth pages: site navigation, heading, honest notice. */
export function AuthShell({ title, lead, children, footer }: AuthShellProps) {
  const locale = useLocale();

  return (
    <main id="main" className="min-h-dvh">
      <SiteNav locale={locale} />
      <section className="mx-auto w-full max-w-md px-6 py-12">
        <h1 className="display text-3xl font-bold text-ink">{title}</h1>
        <p className="mt-3 text-sm text-ink-soft">{lead}</p>
        <div className="mt-8">{children}</div>
        {footer ? <div className="mt-8 text-sm text-ink-soft">{footer}</div> : null}
        <MachineTranslationNotice className="mt-10" />
      </section>
    </main>
  );
}
