import { useId, type HTMLAttributes } from 'react';
import { cn } from '@eco/utils';

/**
 * Eco Nojin brand system.
 *
 * LogoMark   — squircle app icon: sky→leaf→soil gradient with a white
 *              water-drop glyph carrying a sprout cut-out (water gives life).
 * BrandWordmark — Persian-first wordmark: «اکو نوجین» in Vazirmatn ExtraBold
 *              with the brand gradient, over a letter-spaced Latin overline.
 */

export interface LogoMarkProps extends HTMLAttributes<HTMLSpanElement> {
  /** Rendered square size in px. */
  size?: number;
  /** Optional rounded-squircle background. Disable for bare glyph usage. */
  framed?: boolean;
  ariaLabel?: string;
}

export function LogoMark({ size = 32, framed = true, className, ariaLabel = 'اکو نوجین', ...rest }: LogoMarkProps) {
  const uid = useId().replace(/[:]/g, '');
  const bgId = `lnk-bg-${uid}`;
  const inkId = `lnk-ink-${uid}`;
  return (
    <span
      role="img"
      aria-label={ariaLabel}
      className={cn('inline-block shrink-0 select-none', className)}
      style={{ width: size, height: size }}
      {...rest}
    >
      <svg viewBox="0 0 64 64" width="100%" height="100%" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <defs>
          <linearGradient id={bgId} x1="6" y1="4" x2="58" y2="60" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#0e7490" />
            <stop offset="52%" stopColor="#15803d" />
            <stop offset="100%" stopColor="#92400e" />
          </linearGradient>
          <linearGradient id={inkId} x1="6" y1="4" x2="58" y2="60" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#0e7490" />
            <stop offset="52%" stopColor="#15803d" />
            <stop offset="100%" stopColor="#92400e" />
          </linearGradient>
        </defs>

        {framed && (
          <rect width="64" height="64" rx="18" fill={`url(#${bgId})`} />
        )}

        {/* water drop */}
        <path
          d="M32 9C24.5 18.5 17 26 17 36.5a15 15 0 0 0 30 0C47 26 39.5 18.5 32 9z"
          fill={framed ? '#ffffff' : `url(#${inkId})`}
          opacity={framed ? 0.96 : 1}
        />
        {/* sprout cut-out (shows the background through the drop) */}
        <g fill={framed ? `url(#${inkId})` : '#ffffff'}>
          <rect x="30.9" y="30" width="2.2" height="15" rx="1.1" />
          <path d="M30 36.2c-5.6-.4-9.4-3.4-10.4-8.7 5.6.4 9.4 3.4 10.4 8.7z" />
          <path d="M33.2 32.4c.3-5.3 3.5-8.7 8.9-9.6-.3 5.3-3.5 8.7-8.9 9.6z" />
        </g>
      </svg>
    </span>
  );
}

export interface BrandWordmarkProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
  /** 'light' = on light surfaces (gradient type), 'dark' = on dark surfaces. */
  variant?: 'light' | 'dark';
}

const SIZE_MARK: Record<NonNullable<BrandWordmarkProps['size']>, number> = { sm: 24, md: 34, lg: 44 };
const SIZE_TITLE: Record<NonNullable<BrandWordmarkProps['size']>, string> = {
  sm: 'text-sm',
  md: 'text-lg',
  lg: 'text-2xl',
};
const SIZE_OVER: Record<NonNullable<BrandWordmarkProps['size']>, string> = {
  sm: 'text-[8px]',
  md: 'text-[9px]',
  lg: 'text-[11px]',
};

export function BrandWordmark({ size = 'md', variant = 'light', className, ...rest }: BrandWordmarkProps) {
  return (
    <div className={cn('inline-flex items-center gap-2.5', className)} {...rest}>
      <LogoMark size={SIZE_MARK[size]} />
      <span className="flex flex-col leading-none">
        <span
          aria-hidden="true"
          className={cn(
            'font-extrabold tracking-tight',
            SIZE_TITLE[size],
            variant === 'light' ? 'text-gradient-brand' : 'text-white',
          )}
        >
          اکو نوجین
        </span>
        <span className="sr-only">Eco Nojin</span>
        <span
          className={cn(
            'mt-1 font-semibold uppercase tracking-[0.28em]',
            SIZE_OVER[size],
            variant === 'light' ? 'text-ink-muted' : 'text-white/60',
          )}
        >
          Eco Nojin
        </span>
      </span>
    </div>
  );
}
