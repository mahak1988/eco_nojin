'use client';

import { useState } from 'react';
import { cn } from './cn';

export function CurrencyUnitToggle({ className }: { className?: string }) {
  const [unit, setUnit] = useState<'irr' | 'usd'>('irr');
  return (
    <div className={cn('inline-flex rounded-md border border-line p-0.5', className)}>
      {(['irr', 'usd'] as const).map((value) => (
        <button
          key={value}
          type="button"
          aria-pressed={unit === value}
          onClick={() => setUnit(value)}
          className={cn(
            'min-h-9 rounded px-3 text-xs font-semibold uppercase',
            unit === value ? 'bg-forest text-on-action' : 'text-ink-soft',
          )}
        >
          {value}
        </button>
      ))}
    </div>
  );
}
