import { describe, expect, it, vi } from 'vitest';
import {
  buildContactMailto,
  submitContact,
  validateContact,
  type ContactPayload,
} from '../lib/contact';

const valid: ContactPayload = {
  name: 'Hassan Sadeghi',
  email: 'hassan@example.com',
  role: 'Researcher',
  message: 'We would like to join the pilot program this season.',
  locale: 'en',
};

describe('validateContact', () => {
  it('accepts a valid payload', () => {
    expect(validateContact(valid)).toBeNull();
  });

  it('rejects a too-short name', () => {
    expect(validateContact({ ...valid, name: 'H' })).toBe('name');
  });

  it('rejects an invalid email', () => {
    expect(validateContact({ ...valid, email: 'not-an-email' })).toBe('email');
  });

  it('rejects a too-short message', () => {
    expect(validateContact({ ...valid, message: 'hi' })).toBe('message');
  });
});

describe('submitContact', () => {
  it('posts to the gateway endpoint and returns the result', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true, id: 'abc' }), { status: 200 }),
    );
    const result = await submitContact(valid, fetchMock);
    expect(result).toEqual({ ok: true, id: 'abc' });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toContain('/api/v1/contact');
    expect((init as RequestInit).method).toBe('POST');
  });

  it('throws on non-2xx responses', async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response('', { status: 500 }));
    await expect(submitContact(valid, fetchMock)).rejects.toThrow('contact_submit_failed_500');
  });

  it('throws on network failure', async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error('network down'));
    await expect(submitContact(valid, fetchMock)).rejects.toThrow('network down');
  });
});

describe('buildContactMailto', () => {
  it('encodes subject and body', () => {
    const href = buildContactMailto(valid, 'info@econojin.org');
    expect(href.startsWith('mailto:info@econojin.org?')).toBe(true);
    expect(href).toContain(encodeURIComponent('[Researcher] Hassan Sadeghi'));
  });
});
