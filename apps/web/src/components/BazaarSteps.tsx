// Post-scaffold step content components (Phase 3 delivery stubs)
// Each file represents one step of the T05 wizard that will be filled in Phase 3.

import { z } from 'zod';

// Re-export schemas for convenience
export * from '@/lib/validation/bazaar-establishment';

// Step-specific type stubs (Phase 3 will fill these)
export interface Step1BazaarIdentityForm {
  name: string;
  code: string;
  bazaarType: 'rural' | 'inter_village' | 'regional' | 'specialty';
  description: string;
  address: string;
  latitude: number | null;
  longitude: number | null;
}

export interface Step2GeographicBoundaryForm {
  boundingBox: Record<string, unknown> | null;
  areaHa: number | null;
  polygonGeojson: unknown;
}

export interface Step3FoundingBoardForm {
  trustees: Array<{
    fullName: string;
    nationalId: string | null;
    role: string;
    position: number; // 1-5
    phone: string | null;
    email: string | null;
  }>;
}

export interface Step4RulesForm {
  rulesDocument: string | null;
  storeCount: number;
  operatingHours: string | null;
  membershipRules: string | null;
}

export interface Step5VendorsForm {
  vendorIds: string[];
  expectedStoreCount: number | null;
  vendorCategories: string[] | null;
}

export interface Step6SignaturesForm {
  signatures: Array<{
    trusteeId: string;
    stepNumber: number;
    signatureHex: string;
    pqPublicKeyHex: string;
    ciphertextHex: string | null;
    sharedSecretHex: string | null;
    algorithm: string;
    kemAlgorithm: string | null;
  }>;
}

export interface Step7VerificationForm {
  verifiedBy: string | null;
  verificationNotes: string | null;
  verificationDate: string | null;
}

export interface Step8RegistrationForm {
  registrationNumber: string | null;
  registrationDate: string | null;
  regulatorId: string | null;
  systemId: string | null;
}

export interface Step9LaunchForm {
  launchDate: string | null;
  operationalNotes: string | null;
  initialStockCount: number | null;
}

export interface Step10OversightForm {
  oversightSchedule: string | null;
  supportContact: string | null;
  reviewCycleMonths: number | null;
}
