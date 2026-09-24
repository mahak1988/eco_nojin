import { z } from 'zod';

// Step 1: مشخصات بازارچه (Bazaar Identity)
export const step1Schema = z.object({
  name: z.string().min(2, { message: 'نام بازارچه حداقل ۲ کاراکتر' }),
  code: z.string().min(3, { message: 'کد حداقل ۳ کاراکتر' }),
  bazaarType: z.enum(['rural', 'inter_village', 'regional', 'specialty']),
  description: z.string().max(2000).optional(),
  address: z.string().max(500).optional(),
  latitude: z.number().min(-90).max(90).nullable(),
  longitude: z.number().min(-180).max(180).nullable(),
});

// Step 2: محدوده جغرافیایی (Geographic Boundary)
export const step2Schema = z.object({
  boundingBox: z.record(z.string(), z.unknown()).optional(),
  areaHa: z.number().positive().optional(),
  polygonGeojson: z.object({
    type: z.enum(['Polygon', 'MultiPolygon']),
    coordinates: z.array(z.array(z.array(z.number()))),
  }).optional(),
});

// Step 3: هیئت مؤسس ۵ نفره (Founding Board)
export const step3Schema = z.object({
  trustees: z
    .array(
      z.object({
        fullName: z.string().min(2, { message: 'نام کامل حداقل ۲ کاراکتر' }),
        nationalId: z.string().optional(),
        role: z.string().min(2),
        position: z.number().int().min(1).max(5),
        phone: z.string().optional(),
        email: z.string().email().optional(),
      }),
    )
    .length(5, { message: 'دقیقاً ۵ عضو هیئت مؤسس' }),
});

// Step 4: قوانین و ضوابط (Rules)
export const step4Schema = z.object({
  rulesDocument: z.string().optional(),
  storeCount: z.number().int().min(0),
  operatingHours: z.string().optional(),
  membershipRules: z.string().optional(),
});

// Step 5: فروشندگان / فروشگاه‌ها (Vendors)
export const step5Schema = z.object({
  vendorIds: z.array(z.string()).optional(),
  expectedStoreCount: z.number().int().min(0).optional(),
  vendorCategories: z.array(z.string()).optional(),
});

// Step 6: امضای دیجیتال ۵ طرف (5-Party Digital Signatures)
export const step6Schema = z.object({
  signatures: z
    .array(
      z.object({
        trusteeId: z.string(),
        stepNumber: z.number().int(),
        signatureHex: z.string(),
        pqPublicKeyHex: z.string(),
        ciphertextHex: z.string().optional(),
        sharedSecretHex: z.string().optional(),
        algorithm: z.string().optional(),
        kemAlgorithm: z.string().optional(),
      }),
    )
    .min(1),
  });

// Step 7: اعتبارسنجی (Verification)
export const step7Schema = z.object({
  verifiedBy: z.string().optional(),
  verificationNotes: z.string().optional(),
  verificationDate: z.string().optional(),
});

// Step 8: ثبت رسمی (Official Registration)
export const step8Schema = z.object({
  registrationNumber: z.string().optional(),
  registrationDate: z.string().optional(),
  regulatorId: z.string().optional(),
  systemId: z.string().optional(),
});

// Step 9: راه‌اندازی عملیات (Operational Launch)
export const step9Schema = z.object({
  launchDate: z.string().optional(),
  operationalNotes: z.string().optional(),
  initialStockCount: z.number().int().min(0).optional(),
});

// Step 10: نظارت و پشتیبانی (Oversight)
export const step10Schema = z.object({
  oversightSchedule: z.string().optional(),
  supportContact: z.string().optional(),
  reviewCycleMonths: z.number().int().min(1).optional(),
});

// Full form schema (all 10 steps combined)
export const bazaarEstablishmentSchema = z.object({
  step1: step1Schema,
  step2: step2Schema,
  step3: step3Schema,
  step4: step4Schema,
  step5: step5Schema,
  step6: step6Schema,
  step7: step7Schema,
  step8: step8Schema,
  step9: step9Schema,
  step10: step10Schema,
});

export type Step1Input = z.infer<typeof step1Schema>;
export type Step2Input = z.infer<typeof step2Schema>;
export type Step3Input = z.infer<typeof step3Schema>;
export type Step4Input = z.infer<typeof step4Schema>;
export type Step5Input = z.infer<typeof step5Schema>;
export type Step6Input = z.infer<typeof step6Schema>;
export type Step7Input = z.infer<typeof step7Schema>;
export type Step8Input = z.infer<typeof step8Schema>;
export type Step9Input = z.infer<typeof step9Schema>;
export type Step10Input = z.infer<typeof step10Schema>;

export type TrusteeInput = z.infer<typeof step3Schema>['trustees'][number];
export type SignatureInput = z.infer<typeof step6Schema>['signatures'][number];
export type BazaarFormInput = z.infer<typeof bazaarEstablishmentSchema>;
