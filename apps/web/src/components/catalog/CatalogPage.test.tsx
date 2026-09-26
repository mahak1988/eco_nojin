import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { type CatalogEntry, PAGE_CATALOG } from '@/lib/domains/page-catalog';

vi.mock('next-intl/server', () => ({
  setRequestLocale: () => undefined,
  getTranslations: async () => (key: string) => key,
}));

const { CatalogPage } = await import('./CatalogPage');

afterEach(() => {
  cleanup();
});

function pick(predicate: (entry: CatalogEntry) => boolean): CatalogEntry {
  const found = PAGE_CATALOG.find(predicate);
  expect(found, 'no catalog entry matched the predicate').toBeDefined();
  return found as CatalogEntry;
}

async function renderEntry(entry: CatalogEntry) {
  render(await CatalogPage({ locale: 'en', entry }));
}

describe('CatalogPage', () => {
  it('renders the real title and description keys, never a value', async () => {
    const entry = pick((candidate) => candidate.endpoint === null && candidate.routeFile === null);
    await renderEntry(entry);

    expect(screen.getByRole('heading', { level: 1 }).textContent).toBe(
      'market.template.unavailableTitle',
    );
    expect(screen.getByText('market.template.unavailableDescription')).not.toBeNull();
    expect(screen.getByText(entry.description)).not.toBeNull();
  });

  it('shows a StatusDot that matches the registry status', async () => {
    const unavailable = pick((candidate) => candidate.status === 'unavailable');
    await renderEntry(unavailable);
    expect(screen.getByRole('status').textContent).toContain('statusLine.unavailable');
    expect(document.querySelector('.status-dot[data-state="down"]')).not.toBeNull();
    cleanup();

    const planned = pick((candidate) => candidate.status === 'planned');
    await renderEntry(planned);
    expect(screen.getByRole('status').textContent).toContain('common.planned');
    expect(document.querySelector('.status-dot[data-state="warn"]')).not.toBeNull();
  });

  it('stamps provenance as unverified and never claims a verified datum', async () => {
    const entry = pick((candidate) => candidate.endpoint !== null);
    await renderEntry(entry);

    const stamps = document.querySelectorAll('[data-provenance]');
    expect(stamps.length).toBeGreaterThan(0);
    expect(document.querySelector('[data-provenance="verified"]')).toBeNull();
    // Both the entry source and the page-gate document are declared, not observed.
    expect(document.querySelector(`[data-provenance="${entry.sourceOfTruth}"]`)).not.toBeNull();
    expect(
      document.querySelector('[data-provenance="docs/frontend/PAGE_GATES.md"]'),
    ).not.toBeNull();
    expect(screen.getAllByRole('img', { name: 'auth.common.provenance.unverified' }).length).toBe(
      stamps.length,
    );
  });

  it('reports the endpoint, or an explicit unavailable state instead of a stand-in', async () => {
    const withEndpoint = pick((candidate) => candidate.endpoint !== null);
    await renderEntry(withEndpoint);
    expect(screen.getByText(withEndpoint.endpoint as string)).not.toBeNull();
    expect(screen.getByText('statusPage.endpoint')).not.toBeNull();
    cleanup();

    const withoutEndpoint = pick(
      (candidate) => candidate.endpoint === null && candidate.renderedBy === 'catalog-catchall',
    );
    await renderEntry(withoutEndpoint);
    expect(screen.getAllByText('statusLine.unavailable').length).toBeGreaterThan(0);
  });

  it('offers the registry landing page and the live status page as next steps', async () => {
    const entry = pick((candidate) => candidate.domain === 'research');
    await renderEntry(entry);

    const hrefs = screen.getAllByRole('link').map((link) => link.getAttribute('href'));
    expect(hrefs).toContain('/en/research');
    expect(hrefs).toContain('/en/status');
  });

  it('shows the registry owner, gate and access level as declared facts', async () => {
    const entry = pick((candidate) => candidate.domain === 'admin');
    await renderEntry(entry);

    expect(screen.getByText(`${entry.owner} · ${entry.gate} · ${entry.access}`)).not.toBeNull();
    expect(screen.getByRole('heading', { name: 'market.template.contractTitle' })).not.toBeNull();
    expect(screen.getByText('market.template.contractDescription')).not.toBeNull();
  });
});
