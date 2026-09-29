import type { ReactNode } from 'react';

/**
 * Status pill.
 *
 * Tone is a token reference, never a hex value, so a pill in the high-contrast
 * and dark themes picks up the palette instead of fighting it. The dot is
 * `aria-hidden` because the tone is carried by the text label; announcing both
 * would read "success success" to a screen reader.
 */

export type BadgeTone = 'neutral' | 'info' | 'success' | 'warn' | 'bad';
export type BadgeDensity = 'cozy' | 'compact' | 'dense';

export interface BadgeProps {
  children: ReactNode;
  tone?: BadgeTone;
  density?: BadgeDensity;
  /** Shows a leading dot. Decorative; the label carries the meaning. */
  dot?: boolean;
  className?: string;
  title?: string;
}

const TONE_COLOR: Record<BadgeTone, string> = {
  neutral: 'var(--color-ink-soft)',
  info: 'var(--color-sky)',
  success: 'var(--color-forest)',
  warn: 'var(--color-copper)',
  bad: 'var(--color-clay)',
};

const PADDING: Record<BadgeDensity, string> = {
  cozy: 'var(--space-1) var(--space-3)',
  compact: '2px var(--space-2)',
  dense: '0 var(--space-2)',
};

const FONT_SIZE: Record<BadgeDensity, string> = {
  cozy: '0.875rem',
  compact: '0.8125rem',
  dense: '0.75rem',
};

export function Badge({
  children,
  tone = 'neutral',
  density = 'cozy',
  dot = false,
  className = '',
  title,
}: BadgeProps) {
  const color = TONE_COLOR[tone];
  return (
    <span
      className={className}
      title={title}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 'var(--space-1)',
        padding: PADDING[density],
        fontSize: FONT_SIZE[density],
        lineHeight: 1.6,
        borderRadius: 'var(--radius-s)',
        border: `1px solid ${color}`,
        color,
        backgroundColor: 'color-mix(in oklab, currentColor 8%, transparent)',
        whiteSpace: 'nowrap',
      }}
    >
      {dot ? (
        <span
          aria-hidden="true"
          style={{
            inlineSize: '0.5em',
            blockSize: '0.5em',
            borderRadius: '50%',
            backgroundColor: 'currentColor',
          }}
        />
      ) : null}
      {children}
    </span>
  );
}

export default Badge;
