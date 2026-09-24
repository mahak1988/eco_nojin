import type { ReactNode } from 'react';

/** Renders a titled list — used for the T02 «محدودیت‌ها» / «گام بعدی» blocks. */
export function ListBlock({
  title,
  items,
  tone = 'neutral',
  children,
}: {
  title: string;
  items: string[];
  tone?: 'neutral' | 'clay' | 'moss';
  children?: ReactNode;
}) {
  if (items.length === 0 && !children) return null;
  const toneClass = tone === 'clay' ? 'text-clay' : tone === 'moss' ? 'text-moss' : 'field-label';
  return (
    <section
      className="card p-5"
      style={
        tone === 'clay'
          ? { borderColor: 'color-mix(in oklch, var(--clay) 40%, var(--line))' }
          : undefined
      }
    >
      <h2 className={tone === 'neutral' ? 'field-label' : `field-label ${toneClass}`}>{title}</h2>
      {items.length > 0 ? (
        <ul className="mt-3 list-inside list-disc space-y-2 text-sm text-ink">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
      {children}
    </section>
  );
}
