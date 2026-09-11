import { motion, useReducedMotion } from 'framer-motion';
import { useLang } from '../../i18n/LanguageContext';
import type { ReactNode } from 'react';
import Icon from './Icon';
import type { IconKey } from '../../content/site';

export type CardTheme = 'leaf' | 'aqua' | 'sand' | 'night' | 'default';

const themeGradients: Record<CardTheme, string> = {
  leaf: 'linear-gradient(135deg, var(--color-leaf-500)0%, var(--color-leaf-700)100%)',
  aqua: 'linear-gradient(135deg, var(--color-aqua-500)0%, var(--color-aqua-400)100%)',
  sand: 'linear-gradient(135deg, var(--color-sand-500)0%, var(--color-sand-400)100%)',
  night: 'linear-gradient(135deg, var(--color-night-700)0%, var(--color-night-800)100%)',
  default: 'linear-gradient(135deg, var(--color-leaf-500)0%, var(--color-leaf-700)100%)',
};

const themeColors: Record<CardTheme, string> = {
  leaf: 'var(--color-leaf-500)',
  aqua: 'var(--color-aqua-500)',
  sand: 'var(--color-sand-500)',
  night: 'var(--color-aqua-300)',
  default: 'var(--color-leaf-500)',
};

const themeShadows: Record<CardTheme, string> = {
  leaf: '0 24px 48px -12px rgba(47,179,107,0.35)',
  aqua: '0 24px 48px -12px rgba(42,155,181,0.35)',
  sand: '0 24px 48px -12px rgba(212,155,63,0.35)',
  night: '0 24px 48px -12px rgba(126,226,168,0.30)',
  default: '0 24px 48px -12px rgba(47,179,107,0.35)',
};

export interface CardBackContent {
  source?: string;
  method?: string;
  standard?: string;
  frequency?: string;
  apiField?: string;
  status?: string;
  [key: string]: unknown;
}

interface UniversalCardProps {
  title: string;
  desc: string;
  icon?: IconKey;
  iconColor?: string;
  theme?: CardTheme;
  unit?: string;
  badge?: string;
  backContent?: CardBackContent;
  index?: number;
  flipOnHover?: boolean;
  onClick?: () => void;
  children?: ReactNode;
}

/**
 * Enhanced 3D card with gradient background, multi-angle hover tilt,
 * and flip-on-hover effect. Each card has a themed gradient matching
 * its semantic type (leaf/aqua/sand/night).
 *
 * Features:
 * - 135deg gradient per theme (leaf=green, aqua=blue, sand=gold, night=deep teal)
 * - 3D tilt + scale on hover (desktop only)
 * - Flip 180deg to reveal methodology on back
 * - Responsive: h-56 desktop, h-48 tablet, h-44 mobile
 * - Respects prefers-reduced-motion
 */
export default function UniversalCard({
  title,
  desc,
  icon,
  iconColor,
  theme = 'default',
  unit,
  badge,
  backContent,
  index = 0,
  flipOnHover = true,
  onClick,
  children,
}: UniversalCardProps) {
  const { lang } = useLang();
  const reduce = useReducedMotion();
  const bgGradient = themeGradients[theme];
  const iconClr = iconColor || themeColors[theme];
  const shadow = themeShadows[theme];

  if (!flipOnHover || !backContent) {
    return (
      <motion.div
        className="relative h-full w-full overflow-hidden rounded-[1.6rem] [perspective:800px]"
        initial={reduce ? undefined : { opacity: 0, y: 20 }}
        animate={reduce ? undefined : { opacity: 1, y: 0 }}
        transition={{ delay: index * 0.05, duration: 0.5, ease: [0.22, 0.61, 0.36, 1] }}
        onClick={onClick}
      >
        <motion.div
          className="glass glass-hover group relative flex h-full flex-col gap-3 rounded-[1.6rem] p-6 cursor-default"
          style={{
            backgroundImage: bgGradient,
            backgroundBlendMode: 'overlay',
          }}
          whileHover={
            reduce
              ? undefined
              : {
                  scale: 1.03,
                  rotateX: 2,
                  rotateY: 2,
                  boxShadow: shadow,
                }
          }
          transition={{ type: 'spring', stiffness: 350, damping: 25 }}
        >
          {badge ? (
            <span className="text-[10px] font-bold tracking-widest text-[var(--color-night-200)]/50">
              {badge}
            </span>
          ) : null}
          {icon ? (
            <span
              className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl"
              style={{ backgroundColor: `${iconClr}20`, color: iconClr }}
            >
              <Icon name={icon} className="h-5 w-5" aria-hidden />
            </span>
          ) : null}
          {unit ? (
            <span
              className="w-fit rounded-full border border-white/20 bg-white/10 px-3 py-0.5 text-[11px] font-bold text-[var(--color-night-100)]"
              dir="ltr"
            >
              {unit}
            </span>
          ) : null}
          <h3 className="text-base font-extrabold text-[var(--color-night-100)]">{title}</h3>
          <p className="text-sm leading-6 text-[var(--color-night-200)]/70 flex-1">{desc}</p>
          {children ? <div className="mt-auto">{children}</div> : null}
        </motion.div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="relative h-56 w-full [perspective:1000px]"
      initial={reduce ? undefined : { opacity: 0, rotateY: -30 }}
      animate={reduce ? undefined : { opacity: 1, rotateY: 0 }}
      transition={{ delay: index * 0.05, duration: 0.6, ease: [0.220, 0.61, 0.36, 1] }}
    >
      <motion.div
        className="relative h-full w-full [transform-style:preserve-3d]"
        whileHover={
          reduce
            ? undefined
            : {
                rotateY: 180,
                scale: 1.02,
                boxShadow: shadow,
              }
        }
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      >
        {/* front face */}
        <div
          className="absolute inset-0 glass flex flex-col gap-3 rounded-[1.6rem] p-6 [backface-visibility:hidden]"
          style={{
            backgroundImage: bgGradient,
            backgroundBlendMode: 'overlay',
          }}
        >
          {badge ? (
            <span className="text-[10px] font-bold tracking-widest text-[var(--color-night-200)]/50">
              {badge}
            </span>
          ) : null}
          {icon ? (
            <span
              className="inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl"
              style={{ backgroundColor: `${iconClr}25`, color: iconClr }}
            >
              <Icon name={icon} className="h-6 w-6" aria-hidden />
            </span>
          ) : null}
          {unit ? (
            <span
              className="w-fit rounded-full border border-white/20 bg-white/10 px-3 py-0.5 text-[11px] font-bold text-[var(--color-night-100)]"
              dir="ltr"
            >
              {unit}
            </span>
          ) : null}
          <h3 className="text-lg font-extrabold text-[var(--color-night-100)]">{title}</h3>
          <p className="text-sm leading-6 text-[var(--color-night-200)]/70 flex-1">{desc}</p>
          <span className="text-[10px] font-bold text-[var(--color-night-200)]/40">
            {lang === 'fa' ? 'چرخاندن برای جزئیات' : 'Hover to reveal'}
          </span>
        </div>

        {/* back face (methodology) */}
        <div
          className="absolute inset-0 glass flex flex-col gap-4 rounded-[1.6rem] p-6 [backface-visibility:hidden]"
          style={{
            transform: 'rotateY(180deg)',
            backgroundImage: `linear-gradient(135deg, var(--color-night-800)0%, var(--color-night-900)100%)`,
          }}
        >
          <h3 className="text-sm font-extrabold text-[var(--color-night-100)]">
            {lang === 'fa' ? 'جزئیات متریک' : 'Details'}
          </h3>

          {backContent?.source ? (
            <div className="text-xs leading-5 text-[var(--color-night-200)]/60">
              <span className="font-bold text-[var(--color-aqua-300)]">
                {lang === 'fa' ? 'منبع: ' : 'Source: '}
              </span>
              {backContent.source}
            </div>
          ) : null}

          {backContent?.method ? (
            <div className="text-xs leading-5 text-[var(--color-night-200)]/60">
              <span className="font-bold text-[var(--color-aqua-300)]">
                {lang === 'fa' ? 'روش: ' : 'Method: '}
              </span>
              {backContent.method}
            </div>
          ) : null}

          {backContent?.standard ? (
            <div className="rounded-full border border-[var(--color-leaf-500)]/30 bg-[var(--color-leaf-500)]/10 px-3 py-1 text-[10px] font-bold text-[var(--color-leaf-300)]">
              {backContent.standard}
            </div>
          ) : null}

          {backContent?.frequency ? (
            <div className="text-xs text-[var(--color-night-200)]/50">
              {lang === 'fa' ? 'فرکانس: ' : 'Frequency: '}
              {backContent.frequency}
            </div>
          ) : null}

          {backContent?.apiField ? (
            <div className="mt-auto pt-2 text-[10px] font-bold text-[var(--color-leaf-300)]/80 break-all">
              /api/v1/{backContent.apiField}
            </div>
          ) : null}
        </div>
      </motion.div>
    </motion.div>
  );
}
