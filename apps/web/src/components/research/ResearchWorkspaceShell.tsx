'use client';

import { type KeyboardEvent, type ReactNode, useId, useRef, useState } from 'react';

export interface WorkspaceTabItem {
  id: string;
  label: string;
  content: ReactNode;
}

export interface ResearchWorkspaceShellProps {
  /** `id` of the visible heading that names the tabbed region. */
  labelledBy: string;
  tabs: readonly WorkspaceTabItem[];
  /** Left panel: experiment identity, registry and navigation. */
  contextLabel: string;
  context: ReactNode;
  /** Right panel: datasets, runs, validation and provenance sections. */
  sectionsLabel: string;
}

/** Arrow keys follow the writing direction of the surrounding document. */
function isRtlDirection(element: HTMLElement | null): boolean {
  const scoped = element?.closest('[dir]');
  return scoped?.getAttribute('dir') === 'rtl';
}

/**
 * Two-panel research workspace shell.
 *
 * The left panel keeps the experiment identity, the registry contract and the
 * parent return path in view. The right panel groups the evidence sections as
 * an ARIA tab list: every panel is server-rendered, only the inactive ones are
 * hidden, and arrow keys move between tabs in the document writing direction.
 */
export function ResearchWorkspaceShell({
  labelledBy,
  tabs,
  contextLabel,
  context,
  sectionsLabel,
}: ResearchWorkspaceShellProps) {
  const baseId = useId();
  const [activeId, setActiveId] = useState<string>(tabs[0]?.id ?? '');
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});

  function activate(id: string) {
    setActiveId(id);
    tabRefs.current[id]?.focus();
  }

  function move(offset: number) {
    if (tabs.length === 0) return;
    const current = tabs.findIndex((tab) => tab.id === activeId);
    const from = current < 0 ? 0 : current;
    const next = (from + offset + tabs.length) % tabs.length;
    const target = tabs[next];
    if (target) activate(target.id);
  }

  function onKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (tabs.length === 0) return;
    const forward = isRtlDirection(event.currentTarget) ? -1 : 1;
    switch (event.key) {
      case 'ArrowRight':
        event.preventDefault();
        move(forward);
        break;
      case 'ArrowLeft':
        event.preventDefault();
        move(-forward);
        break;
      case 'Home': {
        event.preventDefault();
        const first = tabs[0];
        if (first) activate(first.id);
        break;
      }
      case 'End': {
        event.preventDefault();
        const last = tabs[tabs.length - 1];
        if (last) activate(last.id);
        break;
      }
      default:
        break;
    }
  }

  const contextId = `${baseId}-context`;

  return (
    <div className="mt-6 grid gap-4 lg:grid-cols-2 lg:items-start">
      <section className="card p-5" aria-labelledby={contextId}>
        <h2 id={contextId} className="field-label">
          {contextLabel}
        </h2>
        <div className="mt-3 space-y-4">{context}</div>
      </section>

      <section aria-labelledby={labelledBy}>
        <h2 id={labelledBy} className="field-label">
          {sectionsLabel}
        </h2>
        <div
          role="tablist"
          aria-labelledby={labelledBy}
          aria-orientation="horizontal"
          onKeyDown={onKeyDown}
          className="mt-3 flex flex-wrap gap-2"
        >
          {tabs.map((tab) => {
            const selected = tab.id === activeId;
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                id={`${baseId}-tab-${tab.id}`}
                aria-selected={selected}
                aria-controls={`${baseId}-panel-${tab.id}`}
                tabIndex={selected ? 0 : -1}
                ref={(node) => {
                  tabRefs.current[tab.id] = node;
                }}
                onClick={() => setActiveId(tab.id)}
                className={[
                  'rounded-[var(--radius-m)] border px-3 py-2 text-xs font-semibold transition-micro',
                  selected
                    ? 'border-[var(--line-strong)] bg-[var(--surface-2)] text-[var(--ink)]'
                    : 'border-[var(--line)] bg-[var(--surface)] text-[var(--ink-soft)] hover:text-[var(--ink)]',
                ].join(' ')}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {tabs.map((tab) => (
          <div
            key={tab.id}
            role="tabpanel"
            id={`${baseId}-panel-${tab.id}`}
            aria-labelledby={`${baseId}-tab-${tab.id}`}
            hidden={tab.id !== activeId}
            // biome-ignore lint/a11y/noNoninteractiveTabindex: WAI-ARIA APG requires a focusable tabpanel
            tabIndex={0}
            className="card mt-3 p-5"
          >
            <h3 className="field-label">{tab.label}</h3>
            <div className="mt-3 space-y-4">{tab.content}</div>
          </div>
        ))}
      </section>
    </div>
  );
}
