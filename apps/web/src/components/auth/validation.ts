import { z } from 'zod';
import type { LoginInput, RegisterInput } from '@/lib/bff/contracts';

/**
 * Every user-visible validation string is a message key, never copy.
 * The form renders `t(key)`, so a missing translation degrades to a key
 * instead of leaking English literals into a localized interface.
 */
export const AUTH_VALIDATION_KEYS = [
  'auth.validation.invalid',
  'auth.validation.emailInvalid',
  'auth.validation.passwordRequired',
  'auth.validation.passwordMin',
  'auth.validation.passwordMax',
  'auth.validation.passwordMismatch',
  'auth.validation.fullNameRequired',
  'auth.validation.roleRequired',
  'auth.validation.languageRequired',
  'auth.validation.termsRequired',
  'auth.validation.privacyRequired',
] as const;

export type AuthValidationKey = (typeof AUTH_VALIDATION_KEYS)[number];

const MESSAGE = {
  invalid: 'auth.validation.invalid',
  email: 'auth.validation.emailInvalid',
  passwordRequired: 'auth.validation.passwordRequired',
  passwordMin: 'auth.validation.passwordMin',
  passwordMax: 'auth.validation.passwordMax',
  passwordMismatch: 'auth.validation.passwordMismatch',
  fullName: 'auth.validation.fullNameRequired',
  role: 'auth.validation.roleRequired',
  language: 'auth.validation.languageRequired',
  terms: 'auth.validation.termsRequired',
  privacy: 'auth.validation.privacyRequired',
} as const satisfies Record<string, AuthValidationKey>;

/** Mirrors the role enum accepted by the BFF `registerSchema`. */
export const REGISTER_ROLES = [
  'farmer',
  'researcher',
  'organization',
  'tourist',
  'regular',
] as const satisfies readonly NonNullable<RegisterInput['role']>[];

export type RegisterRole = (typeof REGISTER_ROLES)[number];

/** Mirrors the language enum accepted by the BFF `registerSchema`. */
export const ACCOUNT_LANGUAGES = ['fa', 'en', 'ar'] as const satisfies readonly NonNullable<
  RegisterInput['language']
>[];

export type AccountLanguage = (typeof ACCOUNT_LANGUAGES)[number];

const emailField = z.email({ error: MESSAGE.email });

const loginPasswordField = z
  .string()
  .min(1, { error: MESSAGE.passwordRequired })
  .max(128, { error: MESSAGE.passwordMax });

const signupPasswordField = z
  .string()
  .min(8, { error: MESSAGE.passwordMin })
  .max(128, { error: MESSAGE.passwordMax });

export const loginFormSchema = z.object({
  email: emailField,
  password: loginPasswordField,
});

export const signupFormSchema = z
  .object({
    fullName: z
      .string()
      .trim()
      .min(2, { error: MESSAGE.fullName })
      .max(100, { error: MESSAGE.fullName }),
    email: emailField,
    password: signupPasswordField,
    confirmPassword: z.string().min(1, { error: MESSAGE.passwordRequired }),
    role: z.enum(REGISTER_ROLES, { error: MESSAGE.role }),
    language: z.enum(ACCOUNT_LANGUAGES, { error: MESSAGE.language }),
    acceptTerms: z.literal(true, { error: MESSAGE.terms }),
    acceptPrivacy: z.literal(true, { error: MESSAGE.privacy }),
  })
  .refine((values) => values.password === values.confirmPassword, {
    error: MESSAGE.passwordMismatch,
    path: ['confirmPassword'],
  });

export type LoginFormValues = {
  email: string;
  password: string;
};

/** Raw, unvalidated form values: consent boxes may still be unchecked. */
export type SignupFormValues = {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  role: string;
  language: string;
  acceptTerms: boolean;
  acceptPrivacy: boolean;
};

export type AuthFieldErrors<Field extends string> = Partial<Record<Field, AuthValidationKey>>;

function isValidationKey(value: string): value is AuthValidationKey {
  return (AUTH_VALIDATION_KEYS as readonly string[]).includes(value);
}

function toFieldErrors(error: z.ZodError): Record<string, AuthValidationKey> {
  const collected: Record<string, AuthValidationKey> = {};
  for (const issue of error.issues) {
    const field = issue.path[0];
    if (typeof field !== 'string' || field in collected) continue;
    collected[field] = isValidationKey(issue.message) ? issue.message : MESSAGE.invalid;
  }
  return collected;
}

export function validateLogin(values: unknown): AuthFieldErrors<'email' | 'password'> {
  const result = loginFormSchema.safeParse(values);
  return result.success ? {} : toFieldErrors(result.error);
}

export function validateSignup(values: unknown): AuthFieldErrors<keyof SignupFormValues> {
  const result = signupFormSchema.safeParse(values);
  return result.success ? {} : toFieldErrors(result.error);
}

export function firstInvalidField(
  errors: Partial<Record<string, AuthValidationKey>>,
): string | null {
  const [field] = Object.keys(errors);
  return field ?? null;
}

function formString(data: FormData, name: string): string {
  const value = data.get(name);
  return typeof value === 'string' ? value : '';
}

function formChecked(data: FormData, name: string): boolean {
  return data.get(name) === 'on' || data.get(name) === 'true';
}

/**
 * Builds the raw form values. Email and name are trimmed the same way the BFF
 * `registerSchema` trims them; passwords are never trimmed.
 */
export function readLoginFormValues(data: FormData): LoginFormValues {
  return {
    email: formString(data, 'email').trim(),
    password: formString(data, 'password'),
  };
}

export function readSignupFormValues(data: FormData): SignupFormValues {
  return {
    fullName: formString(data, 'fullName').trim(),
    email: formString(data, 'email').trim(),
    password: formString(data, 'password'),
    confirmPassword: formString(data, 'confirmPassword'),
    role: formString(data, 'role'),
    language: formString(data, 'language'),
    acceptTerms: formChecked(data, 'acceptTerms'),
    acceptPrivacy: formChecked(data, 'acceptPrivacy'),
  };
}

/** Narrows validated form values into the exact BFF payload types. */
export function toLoginPayload(values: LoginFormValues): LoginInput {
  return loginFormSchema.parse(values);
}

export function toRegisterPayload(values: SignupFormValues): RegisterInput {
  const parsed = signupFormSchema.parse(values);
  return {
    email: parsed.email,
    full_name: parsed.fullName,
    password: parsed.password,
    role: parsed.role,
    language: parsed.language,
    accept_tos: parsed.acceptTerms,
    accept_privacy: parsed.acceptPrivacy,
  };
}
