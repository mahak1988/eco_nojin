export type ValidatorFn = (value: string) => string | undefined

export const validators = {
  required:
    (message = 'این فیلد الزامی است'): ValidatorFn =>
    (value) =>
      value.trim() ? undefined : message,

  email:
    (message = 'ایمیل نامعتبر است'): ValidatorFn =>
    (value) =>
      /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? undefined : message,

  password:
    (message = 'رمز عبور باید حداقل ۸ کاراکتر باشد'): ValidatorFn =>
    (value) =>
      value.length >= 8 ? undefined : message,

  passwordStrength:
    (message = 'رمز عبور ضعیف است'): ValidatorFn =>
    (value) => {
      if (value.length < 8) return message
      if (!/[A-Z]/.test(value)) return 'حداقل یک حرف بزرگ نیاز است'
      if (!/[a-z]/.test(value)) return 'حداقل یک حرف کوچک نیاز است'
      if (!/\d/.test(value)) return 'حداقل یک عدد نیاز است'
      if (!/[^A-Za-z0-9]/.test(value)) return 'حداقل یک کاراکتر خاص نیاز است'
      return undefined
    },

  minLength:
    (min: number, message?: string): ValidatorFn =>
    (value) =>
      value.length >= min ? undefined : (message ?? `حداقل ${min} کاراکتر نیاز است`),

  maxLength:
    (max: number, message?: string): ValidatorFn =>
    (value) =>
      value.length <= max ? undefined : (message ?? `حداکثر ${max} کاراکتر مجاز است`),

  match:
    (otherValue: string, message = 'مقادیر مطابقت ندارند'): ValidatorFn =>
    (value) =>
      value === otherValue ? undefined : message,

  otp:
    (message = 'کد باید ۶ رقم باشد'): ValidatorFn =>
    (value) =>
      /^\d{6}$/.test(value) ? undefined : message,

  url:
    (message = 'آدرس وب نامعتبر است'): ValidatorFn =>
    (value) => {
      if (!value) return undefined
      try {
        new URL(value)
        return undefined
      } catch {
        return message
      }
    },
}

export type ValidationRule = {
  validator: ValidatorFn
  message?: string
}

export function validateField(value: string, rules: ValidationRule[]): string | undefined {
  for (const rule of rules) {
    const error = rule.validator(value)
    if (error) return error
  }
  return undefined
}
