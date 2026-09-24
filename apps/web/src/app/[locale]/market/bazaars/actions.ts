// Server Actions for bazaar establishment wizard (Phase 3 scaffold).
// These are Next.js Server Actions that call the API gateway.
// The actual endpoints must exist in the API gateway router.

'use server';

import { revalidatePath } from 'next/cache';
import type { BazaarFormInput } from '@/lib/validation/bazaar-establishment';
import { bazaarEstablishmentSchema } from '@/lib/validation/bazaar-establishment';

export async function establishBazaar(
  prevState: { success: boolean; message: string },
  formData: FormData,
): Promise<{ success: boolean; message: string; bazaarId?: string }> {
  'use server';

  try {
    const raw: Record<string, string> = {};
    for (const [key, value] of formData.entries()) {
      if (typeof value === 'string') raw[key] = value;
    }

    // In Phase 3, this will parse into BazaarFormInput and validate
    // const data = bazaarEstablishmentSchema.parse(raw);

    // TODO: POST to /api/v1/bazaars/establish
    // const response = await fetch(`${API_BASE}/api/v1/bazaars/establish`, {
    //   method: "POST",
    //   headers: { "Content-Type": "application/json" },
    //   body: JSON.stringify(data),
    // });
    // const result = await response.json();

    revalidatePath('/market/bazaars');
    return { success: true, message: 'Bazaar established', bazaarId: 'scaffold' };
  } catch (err) {
    return { success: false, message: String(err) };
  }
}

export async function submitBazaarSignature(
  bazaarId: string,
  trusteeId: string,
  stepNumber: number,
  signatureData: {
    signatureHex: string;
    pqPublicKeyHex: string;
    ciphertextHex?: string;
    sharedSecretHex?: string;
  },
): Promise<{ success: boolean; message: string }> {
  'use server';

  try {
    // TODO: POST to /api/v1/bazaars/{bazaarId}/signatures
    // const response = await fetch(`${API_BASE}/api/v1/bazaars/${bazaarId}/signatures`, {
    //   method: "POST",
    //   headers: { "Content-Type": "application/json" },
    //   body: JSON.stringify({ bazaar_id: bazaarId, trustee_id: trusteeId, step_number: stepNumber, ...signatureData }),
    // });

    return { success: true, message: 'Signature submitted' };
  } catch (err) {
    return { success: false, message: String(err) };
  }
}

export async function verifyBazaarStep(
  bazaarId: string,
  stepNumber: number,
  verifiedBy: string,
): Promise<{ success: boolean; message: string }> {
  'use server';

  try {
    // TODO: POST to /api/v1/bazaars/{bazaarId}/verify
    return { success: true, message: 'Step verified' };
  } catch (err) {
    return { success: false, message: String(err) };
  }
}
