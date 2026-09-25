/**
 * The locale catalogue carries `meta.machineTranslated`; it reaches client
 * components through the `NextIntlClientProvider` messages. The flag decides
 * whether the honest machine-translation notice is rendered.
 */
export function isMachineTranslated(messages: unknown): boolean {
  if (typeof messages !== 'object' || messages === null) return false;
  const meta = (messages as { meta?: unknown }).meta;
  if (typeof meta !== 'object' || meta === null) return false;
  return (meta as { machineTranslated?: unknown }).machineTranslated === true;
}
