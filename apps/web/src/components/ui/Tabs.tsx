'use client';

import { type ReactNode, useId, useRef } from 'react';

import { Card, type CardDensity } from './Card';

/**
 * Tab list with roving tabindex, following the WAI-ARIA tabs pattern.
 *
 * The keyboard contract is the point: a plain row of buttons puts seven stops in
 * the tab order where the pattern calls for one, so a keyboard user traverses
 * every unrelated control on the page to get past a single tab list. Arrow keys
 * move between tabs, Home and End jump to the ends, and only the selected tab is
 * in the tab order.
 *
 * All labels arrive as props. A library that ships its own copy cannot be
 * translated, which is the defect that kept 53 public pages in English.
 */

export type TabDensity = CardDensity;

export interface TabItem {
  id: string;
  label: string;
  /** Announced after the label, e.g. a count. */
  hint?: string;
  disabled?: boolean;
}

export interface TabsProps {
  items: readonly TabItem[];
  activeId: string;
  onChange: (id: string) => void;
  /** Accessible name for the tab list. Required: an unnamed tablist is unusable. */
  label: string;
  density?: TabDensity;
  className?: string;
  children?: ReactNode;
}

const DENSITY_PADDING: Record<TabDensity, string> = {
  cozy: 'var(--space-3) var(--space-5)',
  compact: 'var(--space-2) var(--space-4)',
  dense: 'var(--space-1) var(--space-3)',
};

const DENSITY_FONT: Record<TabDensity, string> = {
  cozy: '1rem',
  compact: '0.875rem',
  dense: '0.8125rem',
};

export function Tabs({
  items,
  activeId,
  onChange,
  label,
  density = 'cozy',
  className = '',
  children,
}: TabsProps) {
  const baseId = useId();
  const listRef = useRef<HTMLDivElement>(null);

  const move = (from: number, delta: number) => {
    const enabled = items.filter((item) => !item.disabled);
    if (enabled.length === 0) return;
    const currentIndex = Math.max(
      0,
      enabled.findIndex((item) => item.id === items[from]?.id),
    );
    const next = (currentIndex + delta + enabled.length) % enabled.length;
    const target = enabled[next];
    onChange(target.id);
    // Move focus with the selection, which is what makes the arrow keys feel
    // like a single control rather than two.
    requestAnimationFrame(() => {
      listRef.current
        ?.querySelector<HTMLButtonElement>(`#${CSS.escape(`${baseId}-${target.id}`)}`)
        ?.focus();
    });
  };

  const handleKeyDown = (event: React.KeyboardEvent, index: number) => {
    switch (event.key) {
      case 'ArrowRight':
        event.preventDefault();
        move(index, 1);
        break;
      case 'ArrowLeft':
        event.preventDefault();
        move(index, -1);
        break;
      case 'Home':
        event.preventDefault();
        move(0, 0);
        listRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]')[0]?.focus();
        break;
      case 'End': {
        event.preventDefault();
        const last = [...items].reverse().find((item) => !item.disabled);
        if (last) {
          onChange(last.id);
          requestAnimationFrame(() => {
            listRef.current
              ?.querySelector<HTMLButtonElement>(`#${CSS.escape(`${baseId}-${last.id}`)}`)
              ?.focus();
          });
        }
        break;
      }
      default:
        break;
    }
  };

  return (
    <div className={className} style={{ display: 'flex', flexDirection: 'column' }}>
      <div
        ref={listRef}
        role="tablist"
        aria-label={label}
        style={{
          display: 'flex',
          gap: 'var(--space-1)',
          borderBottom: '1px solid var(--color-line)',
          overflowX: 'auto',
        }}
      >
        {items.map((item, index) => {
          const selected = item.id === activeId;
          return (
            <button
              key={item.id}
              id={`${baseId}-${item.id}`}
              type="button"
              role="tab"
              aria-selected={selected}
              aria-controls={`${baseId}-${item.id}-panel`}
              // Roving tabindex: one stop for the whole list.
              tabIndex={selected ? 0 : -1}
              disabled={item.disabled}
              onClick={() => onChange(item.id)}
              onKeyDown={(event) => handleKeyDown(event, index)}
              style={{
                padding: DENSITY_PADDING[density],
                fontSize: DENSITY_FONT[density],
                whiteSpace: 'nowrap',
                cursor: item.disabled ? 'not-allowed' : 'pointer',
                border: 0,
                borderBottom: `2px solid ${selected ? 'var(--color-forest)' : 'transparent'}`,
                background: 'transparent',
                color: selected ? 'var(--color-forest)' : 'var(--color-ink-soft)',
                fontWeight: selected ? 600 : 400,
              }}
            >
              {item.label}
              {item.hint ? (
                <span className="num" style={{ marginInlineStart: 'var(--space-2)', opacity: 0.7 }}>
                  {item.hint}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
      {children ? (
        <div
          id={`${baseId}-${activeId}-panel`}
          role="tabpanel"
          aria-labelledby={`${baseId}-${activeId}`}
          style={{ paddingBlockStart: 'var(--space-4)' }}
        >
          {children}
        </div>
      ) : null}
    </div>
  );
}

/** Tab panel for use when the caller wants to own the panel markup. */
export function TabPanel(props: {
  id: string;
  activeId: string;
  children: ReactNode;
  className?: string;
}) {
  const { id, activeId, children, className = '' } = props;
  if (id !== activeId) return null;
  return (
    <div id={`${id}-panel`} role="tabpanel" aria-labelledby={id} className={className}>
      {children}
    </div>
  );
}

export { Card };
export default Tabs;
