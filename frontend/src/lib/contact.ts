/**
 * Contact-form helpers: client-side validation and API submission.
 * The API base URL comes from VITE_API_BASE_URL (defaults to the local gateway).
 */

export type ContactFieldError = 'name' | 'email' | 'message';

export interface ContactPayload {
  name: string;
  email: string;
  role: string;
  message: string;
  locale: string;
  /** Honeypot — must stay empty for real users. */
  website?: string;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/** Returns the first invalid field, or null when the payload is valid. */
export function validateContact(payload: ContactPayload): ContactFieldError | null {
  if (payload.name.trim().length < 2) return 'name';
  if (!EMAIL_RE.test(payload.email.trim())) return 'email';
  if (payload.message.trim().length < 10) return 'message';
  return null;
}

export interface ContactSubmitResult {
  ok: boolean;
  id?: string;
}

/** POSTs the payload to the gateway contact endpoint. Throws on failure. */
export async function submitContact(
  payload: ContactPayload,
  fetchImpl: typeof fetch = fetch,
): Promise<ContactSubmitResult> {
  const base = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
  const response = await fetchImpl(`${base}/api/v1/contact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`contact_submit_failed_${response.status}`);
  }
  return (await response.json()) as ContactSubmitResult;
}

/** Builds the mailto: fallback URL used when the API is unreachable. */
export function buildContactMailto(payload: ContactPayload, to: string): string {
  const subject = `[${payload.role}] ${payload.name}`;
  const body = `Message: ${payload.message}\nName: ${payload.name}\nEmail: ${payload.email}`;
  return `mailto:${to}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}
