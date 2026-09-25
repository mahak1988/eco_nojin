'use server';

import { revalidatePath } from 'next/cache';

/**
 * Bazaar establishment server actions.
 *
 * The bazaar write endpoints these actions used to stub are not connected, so
 * every action now fails explicitly instead of reporting a false success. They
 * are kept only so existing form imports keep resolving.
 */

const UNAVAILABLE = 'This bazaar action is unavailable until its API endpoint is connected.';

export async function establishBazaar(
  _prevState: { success: boolean; message: string },
  _formData: FormData,
): Promise<{ success: boolean; message: string; bazaarId?: string }> {
  'use server';

  revalidatePath('/market/bazaars');
  return { success: false, message: UNAVAILABLE };
}

export async function submitBazaarSignature(
  _bazaarId: string,
  _trusteeId: string,
  _stepNumber: number,
  _signatureData: {
    signatureHex: string;
    pqPublicKeyHex: string;
    ciphertextHex?: string;
    sharedSecretHex?: string;
  },
): Promise<{ success: boolean; message: string }> {
  'use server';

  return { success: false, message: UNAVAILABLE };
}

export async function verifyBazaarStep(
  _bazaarId: string,
  _stepNumber: number,
  _verifiedBy: string,
): Promise<{ success: boolean; message: string }> {
  'use server';

  return { success: false, message: UNAVAILABLE };
}
