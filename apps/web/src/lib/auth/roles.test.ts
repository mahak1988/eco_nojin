import { describe, expect, it } from 'vitest';
import { hasRole, isGlobalRole } from './roles';

describe('role helpers', () => {
  it('accepts canonical global roles', () => {
    expect(isGlobalRole('farmer')).toBe(true);
    expect(isGlobalRole('security_admin')).toBe(true);
  });

  it('rejects an unknown role', () => {
    expect(isGlobalRole('unknown')).toBe(false);
  });

  it('checks explicit role allowlists', () => {
    expect(hasRole('content_admin', ['admin', 'content_admin'])).toBe(true);
    expect(hasRole('farmer', ['admin', 'content_admin'])).toBe(false);
  });
});
