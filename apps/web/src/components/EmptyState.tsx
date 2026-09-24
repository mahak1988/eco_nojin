import type { ReactNode } from 'react';

export function EmptyState({
  message,
  detail,
  action,
}: {
  message: string;
  detail?: string;
  action?: ReactNode;
}) {
  return (
    <div className="card flex flex-col items-start gap-2 px-5 py-4">
      <p className="text-sm text-ink">{message}</p>
      {detail ? <p className="num text-xs text-ink-faint">{detail}</p> : null}
      {action}
    </div>
  );
}
