/** Shared API helpers: gateway base URL, newsletter and pilot submissions. */

export function getApiBase(): string {
  return import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';
}

export interface NewsletterResult {
  ok: boolean;
  already?: boolean;
}

/** Subscribes an email to the newsletter via POST /api/v1/newsletter/subscribe. */
export async function subscribeNewsletter(
  email: string,
  locale: string,
  fetchImpl: typeof fetch = fetch,
): Promise<NewsletterResult> {
  const response = await fetchImpl(`${getApiBase()}/api/v1/newsletter/subscribe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, locale }),
  });
  if (!response.ok) {
    throw new Error(`newsletter_subscribe_failed_${response.status}`);
  }
  return (await response.json()) as NewsletterResult;
}

export interface PilotPayload {
  name: string;
  phone: string;
  province: string;
  land_hectares?: number | null;
  main_crop?: string | null;
  preferred_channel?: string | null;
  consent: boolean;
  locale: string;
}

/** Submits a pilot interest application via POST /api/v1/pilot/apply. */
export async function submitPilotApplication(
  payload: PilotPayload,
  fetchImpl: typeof fetch = fetch,
): Promise<{ ok: boolean; id?: string }> {
  const response = await fetchImpl(`${getApiBase()}/api/v1/pilot/apply`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`pilot_apply_failed_${response.status}`);
  }
  return (await response.json()) as { ok: boolean; id?: string };
}

export function validatePilot(payload: PilotPayload): boolean {
  return (
    payload.name.trim().length >= 2 &&
    payload.phone.trim().length >= 7 &&
    payload.province.trim().length >= 2 &&
    payload.consent === true
  );
}
