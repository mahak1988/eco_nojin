import { z } from 'zod';

export const step1Schema = z.object({
  bazaarId: z.string().min(1, 'بازارچه الزامی است'),
  storeName: z.string().min(2, 'نام فروشگاه باید حداقل ۲ کاراکتر باشد'),
  storeCode: z.string().min(2, 'کد فروشگاه باید حداقل ۲ کاراکتر باشد'),
  storeType: z.enum(['producer', 'reseller', 'cooperative', 'artisan']),
  ownerName: z.string().min(2, 'نام مالک باید حداقل ۲ کاراکتر باشد'),
  contactPhone: z.string().min(10, 'شماره تماس نامعتبر است'),
  contactEmail: z.string().email('ایمیل نامعتبر است').optional().or(z.literal('')),
});

export const step2Schema = z.object({
  description: z.string().max(2000, 'توضیحات نباید بیشتر از ۲۰۰۰ کاراکتر باشد').optional(),
  address: z.string().min(5, 'آدرس باید حداقل ۵ کاراکتر باشد').optional(),
  latitude: z.number().min(-90).max(90).optional(),
  longitude: z.number().min(-180).max(180).optional(),
  website: z.string().url('آدرس وب‌سایت نامعتبر است').optional().or(z.literal('')),
  socialLinks: z.string().optional(),
});

export const step3Schema = z.object({
  inventoryCategories: z.array(z.string()).optional(),
  initialStockCount: z.number().min(0).optional(),
  stockValue: z.number().min(0).optional(),
});

export const step4Schema = z.object({
  pricingStrategy: z.enum(['fixed', 'dynamic', 'tiered']).optional(),
  baseCurrency: z.string().length(3).optional(),
  taxIncluded: z.boolean().optional(),
});

export const step5Schema = z.object({
  shippingMethods: z.array(z.enum(['standard', 'express', 'pickup', 'freight'])).optional(),
  shippingZones: z.array(z.string()).optional(),
  freeShippingThreshold: z.number().min(0).optional(),
});

export const step6Schema = z.object({
  paymentMethods: z.array(z.enum(['wallet', 'card', 'bank_transfer', 'cash', 'installment'])).optional(),
  escrowRequired: z.boolean().optional(),
  installmentMonths: z.number().min(1).max(24).optional(),
});

export const step7Schema = z.object({
  complianceDocs: z.array(z.string()).optional(),
  certifications: z.array(z.string()).optional(),
  insurancePolicy: z.string().optional(),
});

export const step8Schema = z.object({
  launchDate: z.string().optional(),
  initialStockCount: z.number().min(0).optional(),
  operationalNotes: z.string().optional(),
});

export type Step1Input = z.infer<typeof step1Schema>;
export type Step2Input = z.infer<typeof step2Schema>;
export type Step3Input = z.infer<typeof step3Schema>;
export type Step4Input = z.infer<typeof step4Schema>;
export type Step5Input = z.infer<typeof step5Schema>;
export type Step6Input = z.infer<typeof step6Schema>;
export type Step7Input = z.infer<typeof step7Schema>;
export type Step8Input = z.infer<typeof step8Schema>;

export const storeCreationSchema = z.object({
  step1: step1Schema,
  step2: step2Schema,
  step3: step3Schema,
  step4: step4Schema,
  step5: step5Schema,
  step6: step6Schema,
  step7: step7Schema,
  step8: step8Schema,
});

export type StoreCreationInput = z.infer<typeof storeCreationSchema>;