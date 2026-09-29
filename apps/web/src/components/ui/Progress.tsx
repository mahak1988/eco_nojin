/**
 * Determinate and indeterminate progress indicator.
 *
 * `aria-valuenow` is omitted for an indeterminate bar, which is what tells a
 * screen reader the value is unknown. Supplying 0 instead reads as "zero per
 * cent complete", which is a different and wrong claim.
 *
 * The label is required: a bare bar tells a non-visual user nothing.
 */

export type ProgressTone = 'info' | 'success' | 'warn' | 'bad';
export type ProgressSize = 'cozy' | 'compact' | 'dense';

export interface ProgressProps {
  /** Accessible name. Also rendered visibly unless `hideLabel`. */
  label: string;
  /** 0–100. Omit for an indeterminate bar. */
  value?: number;
  max?: number;
  tone?: ProgressTone;
  size?: ProgressSize;
  hideLabel?: boolean;
  /** Announced after the label, e.g. "3 of 51". */
  detail?: string;
  className?: string;
}

const TONE_COLOR: Record<ProgressTone, string> = {
  info: 'var(--color-water)',
  success: 'var(--color-forest)',
  warn: 'var(--color-copper)',
  bad: 'var(--color-clay)',
};

const TRACK_HEIGHT: Record<ProgressSize, string> = {
  cozy: '0.75rem',
  compact: '0.5rem',
  dense: '0.375rem',
};

export function Progress({
  label,
  value,
  max = 100,
  tone = 'info',
  size = 'cozy',
  hideLabel = false,
  detail,
  className = '',
}: ProgressProps) {
  const indeterminate = value === undefined;
  const clamped = indeterminate ? 0 : Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div
      className={className}
      style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}
    >
      {!hideLabel ? (
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '0.875rem',
            color: 'var(--color-ink-soft)',
          }}
        >
          <span>{label}</span>
          {detail ? <span className="num">{detail}</span> : null}
        </div>
      ) : null}
      <div
        role="progressbar"
        aria-label={hideLabel ? label : undefined}
        aria-valuemin={indeterminate ? undefined : 0}
        aria-valuemax={indeterminate ? undefined : max}
        aria-valuenow={indeterminate ? undefined : clamped}
        aria-valuetext={indeterminate ? undefined : `${Math.round(clamped)}%`}
        style={{
          blockSize: TRACK_HEIGHT[size],
          borderRadius: 'var(--radius-s)',
          backgroundColor: 'var(--color-surface-2)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            blockSize: '100%',
            inlineSize: indeterminate ? '40%' : `${clamped}%`,
            backgroundColor: TONE_COLOR[tone],
            borderRadius: 'inherit',
            transition: indeterminate
              ? undefined
              : 'inline-size var(--duration-240) var(--easing-ease-out)',
            ...(indeterminate ? { animation: 'progress-slide 1.4s ease-in-out infinite' } : {}),
          }}
        />
      </div>
      <style>{`
        @keyframes progress-slide {
          0% { margin-inline-start: -40%; }
          100% { margin-inline-start: 100%; }
        }
        @media (prefers-reduced-motion: reduce) {
          .progress-indeterminate { animation: none; }
        }
      `}</style>
    </div>
  );
}

export default Progress;
