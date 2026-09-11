/** Shared API helpers: gateway base URL, newsletter and pilot submissions.
 * The base URL can be overridden from the dashboard settings page
 * (localStorage: hydroma-api-base). */

export function getApiBase(): string {
  try {
    const override = localStorage.getItem('hydroma-api-base');
    if (override && /^https?:\/\//.test(override.trim())) return override.trim().replace(/\/$/, '');
  } catch {
    /* localStorage unavailable — fall through to default */
  }
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

export interface PilotFilePayload extends PilotPayload {
  file?: File | null;
}

export async function submitPilotApplication(
  payload: PilotPayload,
  fetchImpl: typeof fetch = fetch,
): Promise<{ ok: boolean; id?: string }> {
  const hasFile = 'file' in payload && (payload as PilotFilePayload).file instanceof File;

  const headers: Record<string, string> = {};
  let body: BodyInit;

  if (hasFile) {
    const form = new FormData();
    const filePayload = payload as PilotFilePayload;
    form.append('name', filePayload.name);
    form.append('phone', filePayload.phone);
    form.append('province', filePayload.province);
    form.append('consent', String(filePayload.consent));
    form.append('locale', filePayload.locale);
    if (filePayload.land_hectares != null) form.append('land_hectares', String(filePayload.land_hectares));
    if (filePayload.main_crop != null) form.append('main_crop', filePayload.main_crop);
    if (filePayload.preferred_channel != null) form.append('preferred_channel', filePayload.preferred_channel);
    if (filePayload.file) form.append('file', filePayload.file);
    body = form;
  } else {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(payload);
  }

  const response = await fetchImpl(`${getApiBase()}/api/v1/pilot/apply`, {
    method: 'POST',
    headers,
    body,
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
