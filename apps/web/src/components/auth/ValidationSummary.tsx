'use client';

import { useAuthMessage } from './useAuthMessage';
import type { AuthValidationKey } from './validation';

export interface ValidationSummaryProps {
  errors: Partial<Record<string, AuthValidationKey>>;
  onFocusField: (name: string) => void;
}

/**
 * Accessible summary of a failed client-side validation pass. Each entry is a
 * control that moves focus to the offending field, so keyboard and screen
 * reader users reach the problem without hunting for it.
 */
export function ValidationSummary({ errors, onFocusField }: ValidationSummaryProps) {
  const t = useAuthMessage();
  const entries = Object.entries(errors).filter(
    (entry): entry is [string, AuthValidationKey] => entry[1] !== undefined,
  );
  if (entries.length === 0) return null;

  return (
    <div
      role="alert"
      className="rounded-[var(--radius-card)] border border-line bg-surface p-4 text-start"
    >
      <p className="text-sm font-semibold text-[var(--copper)]">
        {t('auth.common.validationHeading')}
      </p>
      <ul className="mt-2 list-disc space-y-1 ps-5 text-sm">
        {entries.map(([field, key]) => (
          <li key={field}>
            <button
              type="button"
              onClick={() => onFocusField(field)}
              className="text-start text-water underline underline-offset-2"
            >
              {t(key)}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
