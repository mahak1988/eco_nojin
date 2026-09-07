import { type ReactNode } from 'react';
import { cn } from '@eco/utils';

export type MascotProps = {
  name?: string;
  size?: number;
  className?: string;
  emotion?: 'happy' | 'thinking' | 'excited' | 'sleepy';
  animated?: boolean;
};

const MASCOT_EMOJIS: Record<string, ReactNode> = {
  happy: '🌱',
  thinking: '🤔',
  excited: '🌿',
  sleepy: '😴',
};

const DEFAULT_EMOJI: ReactNode = '🌱';

export function Mascot({
  name = 'Eco',
  size = 64,
  className,
  emotion = 'happy',
  animated = true,
}: MascotProps) {
  const emoji = (MASCOT_EMOJIS as Record<string, ReactNode>)[emotion] ?? DEFAULT_EMOJI;

  return (
    <div
      className={cn('inline-flex items-center justify-center rounded-full bg-brand-50', className)}
      style={{ width: size, height: size }}
      aria-label={`${name} the mascot`}
      role="img"
    >
      <span
        className={cn(
          'select-none',
          animated && 'animate-bounce',
        )}
        style={{ fontSize: size * 0.6 }}
      >
        {emoji}
      </span>
    </div>
  );
}
