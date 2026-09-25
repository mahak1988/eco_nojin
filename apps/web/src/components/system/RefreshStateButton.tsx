'use client';

import { useTransition } from 'react';
import { useRouter } from '@/i18n/navigation';

export function RefreshStateButton({ label }: { label: string }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  return (
    <button
      type="button"
      className="btn btn-ghost"
      disabled={pending}
      aria-busy={pending}
      onClick={() => startTransition(() => router.refresh())}
    >
      {label}
    </button>
  );
}
