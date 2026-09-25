import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { workspaceNavigationForRole } from '@/lib/workspaces/registry';
import { WorkspaceNav } from './WorkspaceNav';

vi.mock('next-intl', () => ({
  useLocale: () => 'en',
  useTranslations: () => (key: string) => key.split('.').at(-1) ?? key,
}));

vi.mock('next/navigation', () => ({
  usePathname: () => '/en/workspace/audit',
}));

afterEach(() => {
  cleanup();
});

describe('WorkspaceNav', () => {
  it('renders one named navigation landmark and grouped entries', () => {
    render(<WorkspaceNav groups={workspaceNavigationForRole('admin')} sessionRole="admin" />);

    expect(screen.getByRole('navigation', { name: 'mainNav' })).not.toBeNull();
    expect(screen.getByText('/en/workspace')).not.toBeNull();
    expect(screen.getByRole('heading', { name: 'work' })).not.toBeNull();
    expect(screen.getByRole('heading', { name: 'operations' })).not.toBeNull();
  });

  it('marks only the current location with aria-current', () => {
    render(<WorkspaceNav groups={workspaceNavigationForRole('admin')} sessionRole="admin" />);

    const current = screen
      .getAllByRole('link')
      .filter((link) => link.getAttribute('aria-current') === 'page');
    expect(current).toHaveLength(1);
    expect(current[0].getAttribute('href')).toBe('/en/workspace/audit');
  });

  it('shows the locale-neutral route for every entry', () => {
    render(<WorkspaceNav groups={workspaceNavigationForRole('admin')} sessionRole="admin" />);

    const hrefs = screen.getAllByRole('link').map((link) => link.getAttribute('href'));
    expect(hrefs).toContain('/en/workspace/operations/health');
    expect(hrefs).toContain('/en/workspace/settings/access');
  });

  it('hides entries outside the role scope without hiding the surface', () => {
    render(<WorkspaceNav groups={workspaceNavigationForRole('advisor')} sessionRole="advisor" />);

    const hrefs = screen.getAllByRole('link').map((link) => link.getAttribute('href'));
    expect(hrefs).toContain('/en/workspace/assignments');
    expect(hrefs).toContain('/en/workspace/knowledge');
    expect(hrefs).not.toContain('/en/workspace/audit');
    expect(hrefs).not.toContain('/en/workspace/team');
  });

  it('renders no link at all for a role outside the allowlist', () => {
    render(<WorkspaceNav groups={workspaceNavigationForRole('farmer')} sessionRole="farmer" />);

    expect(screen.queryAllByRole('link')).toHaveLength(0);
    expect(screen.getByText('unavailable')).not.toBeNull();
  });

  it('never reads a role from browser storage', () => {
    window.localStorage.clear();
    render(<WorkspaceNav groups={workspaceNavigationForRole('analyst')} sessionRole="analyst" />);

    expect(window.localStorage.length).toBe(0);
  });
});
