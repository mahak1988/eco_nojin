import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { ResearchWorkspaceShell, type WorkspaceTabItem } from './ResearchWorkspaceShell';

afterEach(() => {
  cleanup();
});

const tabs: WorkspaceTabItem[] = [
  { id: 'datasets', label: 'Datasets', content: <p>dataset panel</p> },
  { id: 'runs', label: 'Runs', content: <p>run panel</p> },
  { id: 'validation', label: 'Validation', content: <p>validation panel</p> },
];

function renderShell(dir: 'ltr' | 'rtl' = 'ltr') {
  return render(
    <div dir={dir}>
      <ResearchWorkspaceShell
        labelledBy="sections"
        sectionsLabel="Sections"
        contextLabel="Contract"
        context={<p>context panel</p>}
        tabs={tabs}
      />
      ,
    </div>,
  );
}

describe('ResearchWorkspaceShell', () => {
  it('renders a named tab list with a two-panel workspace layout', () => {
    renderShell();

    expect(screen.getByRole('tablist', { name: 'Sections' })).not.toBeNull();
    expect(screen.getByRole('heading', { name: 'Contract' })).not.toBeNull();
    expect(screen.getAllByRole('tab')).toHaveLength(3);
    expect(screen.getByText('context panel')).not.toBeNull();
  });

  it('shows the first panel and hides the rest', () => {
    renderShell();

    const selected = screen
      .getAllByRole('tab')
      .filter((tab) => tab.getAttribute('aria-selected') === 'true');
    expect(selected).toHaveLength(1);
    expect(selected[0].textContent).toBe('Datasets');
    expect(screen.getByRole('tabpanel').textContent).toContain('dataset panel');
  });

  it('selects a panel on click and links tab to panel', () => {
    renderShell();

    const runsTab = screen.getAllByRole('tab')[1];
    const panelId = runsTab.getAttribute('aria-controls');
    expect(panelId).not.toBeNull();

    fireEvent.click(runsTab);

    expect(runsTab.getAttribute('aria-selected')).toBe('true');
    expect(document.getElementById(panelId as string)?.getAttribute('aria-labelledby')).toBe(
      runsTab.getAttribute('id'),
    );
    expect(screen.getByRole('tabpanel').textContent).toContain('run panel');
  });

  it('moves between tabs with arrow keys and keeps a single tab stop', () => {
    renderShell();

    const tablist = screen.getByRole('tablist');
    const first = screen.getAllByRole('tab')[0];

    expect(screen.getAllByRole('tab').map((tab) => tab.getAttribute('tabindex'))).toEqual([
      '0',
      '-1',
      '-1',
    ]);

    fireEvent.keyDown(tablist, { key: 'ArrowRight' });
    expect(screen.getAllByRole('tab')[1].getAttribute('aria-selected')).toBe('true');
    expect(document.activeElement).toBe(screen.getAllByRole('tab')[1]);

    fireEvent.keyDown(tablist, { key: 'End' });
    expect(screen.getAllByRole('tab')[2].getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(tablist, { key: 'Home' });
    expect(first.getAttribute('aria-selected')).toBe('true');
  });

  it('follows the writing direction for horizontal navigation', () => {
    renderShell('rtl');
    const tablist = screen.getByRole('tablist');
    const tabs = () => screen.getAllByRole('tab');

    // In RTL the visual order is reversed, so ArrowRight walks backwards.
    fireEvent.keyDown(tablist, { key: 'ArrowRight' });
    expect(tabs()[2].getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(tablist, { key: 'ArrowRight' });
    expect(tabs()[1].getAttribute('aria-selected')).toBe('true');

    fireEvent.keyDown(tablist, { key: 'ArrowLeft' });
    expect(tabs()[2].getAttribute('aria-selected')).toBe('true');
  });

  it('ignores unrelated keys', () => {
    renderShell();
    const tablist = screen.getByRole('tablist');

    fireEvent.keyDown(tablist, { key: 'a' });

    expect(screen.getAllByRole('tab')[0].getAttribute('aria-selected')).toBe('true');
  });
});
