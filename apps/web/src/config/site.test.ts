import { afterEach, describe, expect, it, vi } from 'vitest';

const FALLBACK = 'https://app.eco-nojin.org';

async function loadSiteUrl(value?: string) {
  vi.resetModules();
  if (value === undefined) {
    vi.stubEnv('NEXT_PUBLIC_SITE_URL', undefined);
  } else {
    vi.stubEnv('NEXT_PUBLIC_SITE_URL', value);
  }
  const module = await import('@/config/site');
  return module.SITE_URL;
}

describe('SITE_URL', () => {
  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it('falls back to the production origin when the environment has no value', async () => {
    expect(await loadSiteUrl()).toBe(FALLBACK);
  });

  it('falls back when the environment value is empty or whitespace', async () => {
    expect(await loadSiteUrl('')).toBe(FALLBACK);
    expect(await loadSiteUrl('   ')).toBe(FALLBACK);
  });

  it('uses the configured origin when present', async () => {
    expect(await loadSiteUrl('http://localhost:3001')).toBe('http://localhost:3001');
  });

  it('strips trailing slashes so path joins never double up', async () => {
    expect(await loadSiteUrl('https://staging.eco-nojin.org/')).toBe(
      'https://staging.eco-nojin.org',
    );
    expect(await loadSiteUrl('https://staging.eco-nojin.org///')).toBe(
      'https://staging.eco-nojin.org',
    );
  });

  it('trims surrounding whitespace from the configured origin', async () => {
    expect(await loadSiteUrl(' https://staging.eco-nojin.org/ ')).toBe(
      'https://staging.eco-nojin.org',
    );
  });
});
