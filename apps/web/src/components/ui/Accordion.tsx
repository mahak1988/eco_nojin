'use client';

import { type ReactNode, useId, useState } from 'react';

/**
 * Disclosure group following the WAI-ARIA accordion pattern.
 *
 * Uses `aria-expanded` plus `aria-controls` on a real `<button>` rather than
 * `<details>`, because the platform needs to control animation and because
 * `details` cannot be styled to the design system's density scale without
 * fighting the browser's own marker.
 *
 * Labels arrive as props so the component carries no translatable copy.
 */

export type AccordionDensity = 'cozy' | 'compact' | 'dense';

export interface AccordionItem {
  id: string;
  /** The always-visible trigger text. */
  title: string;
  /** Optional secondary line inside the trigger. */
  summary?: string;
  disabled?: boolean;
  content: ReactNode;
}

export interface AccordionProps {
  items: readonly AccordionItem[];
  /** Accessible name for the group. */
  label: string;
  /** Ids expanded on first render. */
  defaultExpanded?: readonly string[];
  /** Only one panel open at a time. */
  exclusive?: boolean;
  density?: AccordionDensity;
  className?: string;
  onToggle?: (id: string, expanded: boolean) => void;
}

const DENSITY: Record<
  AccordionDensity,
  { padding: string; panel: string; title: string; gap: string }
> = {
  cozy: {
    padding: 'var(--space-4)',
    panel: 'var(--space-4)',
    title: '1rem',
    gap: 'var(--space-3)',
  },
  compact: {
    padding: 'var(--space-3)',
    panel: 'var(--space-3)',
    title: '0.9375rem',
    gap: 'var(--space-2)',
  },
  dense: {
    padding: 'var(--space-2)',
    panel: 'var(--space-2)',
    title: '0.875rem',
    gap: 'var(--space-1)',
  },
};

const triggerBase: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  gap: 'var(--space-3)',
  inlineSize: '100%',
  textAlign: 'start',
  background: 'transparent',
  border: 0,
  cursor: 'pointer',
  color: 'var(--color-ink)',
  font: 'inherit',
};

export function Accordion({
  items,
  label,
  defaultExpanded = [],
  exclusive = false,
  density = 'cozy',
  className = '',
  onToggle,
}: AccordionProps) {
  const baseId = useId();
  const [expanded, setExpanded] = useState<Set<string>>(new Set(defaultExpanded));
  const scale = DENSITY[density];

  const toggle = (id: string) => {
    setExpanded((previous) => {
      const next = new Set(previous);
      if (next.has(id)) {
        next.delete(id);
      } else {
        if (exclusive) next.clear();
        next.add(id);
      }
      onToggle?.(id, next.has(id));
      return next;
    });
  };

  return (
    // `<section>` carries the group name to assistive technology. An earlier
    // version used `role="group"` on a div with a `hidden` span holding the
    // label; a hidden element leaves the accessibility tree, so that announced
    // nothing at all.
    <section
      className={className}
      aria-label={label}
      style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}
    >
      {items.map((item) => {
        const isOpen = expanded.has(item.id);
        return (
          <div
            key={item.id}
            style={{ border: '1px solid var(--color-line)', borderRadius: 'var(--radius-m)' }}
          >
            <h3 style={{ margin: 0 }}>
              <button
                type="button"
                id={`${baseId}-${item.id}-trigger`}
                aria-expanded={isOpen}
                aria-controls={`${baseId}-${item.id}-panel`}
                disabled={item.disabled}
                onClick={() => toggle(item.id)}
                style={{ ...triggerBase, padding: scale.padding, opacity: item.disabled ? 0.5 : 1 }}
              >
                <span style={{ display: 'flex', flexDirection: 'column', gap: scale.gap }}>
                  <span style={{ fontWeight: 600, fontSize: scale.title }}>{item.title}</span>
                  {item.summary ? (
                    <span style={{ fontSize: '0.875rem', color: 'var(--color-ink-soft)' }}>
                      {item.summary}
                    </span>
                  ) : null}
                </span>
                <span
                  aria-hidden="true"
                  style={{
                    flexShrink: 0,
                    color: 'var(--color-ink-faint)',
                    transform: isOpen ? 'rotate(90deg)' : 'none',
                    transition: 'transform var(--duration-120) var(--easing-ease-out)',
                  }}
                >
                  ›
                </span>
              </button>
            </h3>
            {isOpen ? (
              <section
                id={`${baseId}-${item.id}-panel`}
                aria-labelledby={`${baseId}-${item.id}-trigger`}
                style={{ padding: `0 var(--space-4) ${scale.panel}` }}
              >
                {item.content}
              </section>
            ) : null}
          </div>
        );
      })}
    </section>
  );
}

export default Accordion;
