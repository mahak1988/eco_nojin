import { cn } from '@eco/utils'
import { type ChangeEvent, type FormEvent, useState } from 'react'
import { Button } from '../../primitives'
import { Field } from '../../primitives'
import { Input } from '../../primitives'
import { Checkbox } from '../../primitives'
import { type StepItem, Stepper } from '../../primitives'
import { type ValidationRule, validateField, validators } from '../../utils/validators'
import { AlertBanner } from '../alert-banner'

export type RegisterFormProps = {
  onSubmit: (data: RegisterData) => Promise<void> | void
  onSignIn?: () => void
  className?: string
}

export type RegisterData = {
  email: string
  password: string
  confirmPassword: string
  name: string
  acceptTerms: boolean
}

const STEPS: StepItem[] = [{ label: 'حساب کاربری' }, { label: 'پروفایل' }, { label: 'تایید' }]

const EMAIL_RULES: ValidationRule[] = [
  { validator: validators.required('ایمیل الزامی است') },
  { validator: validators.email('ایمیل نامعتبر است') },
]

const PASSWORD_RULES: ValidationRule[] = [
  { validator: validators.required('رمز عبور الزامی است') },
  { validator: validators.minLength(8, 'رمز عبور باید حداقل ۸ کاراکتر باشد') },
  { validator: validators.passwordStrength('رمز عبور ضعیف است') },
]

const NAME_RULES: ValidationRule[] = [
  { validator: validators.required('نام الزامی است') },
  { validator: validators.minLength(2, 'نام باید حداقل ۲ کاراکتر باشد') },
]

function passwordStrength(password: string): number {
  let score = 0
  if (password.length >= 8) score++
  if (/[A-Z]/.test(password)) score++
  if (/[a-z]/.test(password)) score++
  if (/\d/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++
  return score
}

export function RegisterForm({ onSubmit, onSignIn, className }: RegisterFormProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [formData, setFormData] = useState<RegisterData>({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    acceptTerms: false,
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const updateField = (field: keyof RegisterData, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
    if (typeof value === 'string') {
      const rules =
        field === 'email'
          ? EMAIL_RULES
          : field === 'password'
            ? PASSWORD_RULES
            : field === 'name'
              ? NAME_RULES
              : []
      const error = validateField(value, rules)
      setErrors((prev) => ({ ...prev, [field]: error ?? '' }))
    }
  }

  const validateStep = (step: number): boolean => {
    const stepErrors: Record<string, string> = {}

    if (step === 0) {
      const emailError = validateField(formData['email'], EMAIL_RULES)
      const passwordError = validateField(formData['password'], PASSWORD_RULES)
      const confirmError = formData['confirmPassword']
        ? validateField(formData['confirmPassword'], [
            { validator: validators.match(formData['password'], 'رمز عبور مطابقت ندارد') },
          ])
        : undefined
      if (emailError) stepErrors['email'] = emailError
      if (passwordError) stepErrors['password'] = passwordError
      if (confirmError) stepErrors['confirmPassword'] = confirmError
    } else if (step === 1) {
      const nameError = validateField(formData['name'], NAME_RULES)
      if (nameError) stepErrors['name'] = nameError
    } else if (step === 2) {
      if (!formData['acceptTerms']) stepErrors['acceptTerms'] = 'پذیرش شرایط الزامی است'
    }

    setErrors((prev) => ({ ...prev, ...stepErrors }))
    return Object.keys(stepErrors).length === 0
  }

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep((s) => Math.min(STEPS.length - 1, s + 1))
    }
  }

  const handleBack = () => setCurrentStep((s) => Math.max(0, s - 1))

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setServerError(null)

    if (!validateStep(currentStep)) return

    setLoading(true)
    try {
      await onSubmit(formData)
    } catch (err) {
      setServerError(err instanceof Error ? err.message : 'خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.')
    } finally {
      setLoading(false)
    }
  }

  const strength = passwordStrength(formData['password'])

  return (
    <div className={cn('w-full', className)}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
        {serverError && <AlertBanner tone="danger">{serverError}</AlertBanner>}

        <Stepper steps={STEPS} currentStep={currentStep} />

        <div className="rounded-lg border border-ink/10 bg-surface-raised p-5">
          {currentStep === 0 && (
            <div className="flex flex-col gap-4">
              <Field label="ایمیل" error={errors['email']}>
                <Input
                  type="email"
                  value={formData['email']}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    updateField('email', e.target.value)
                  }
                  placeholder="you@example.com"
                  invalid={!!errors['email']}
                  disabled={loading}
                  autoComplete="email"
                  inputMode="email"
                />
              </Field>

              <Field label="رمز عبور" error={errors['password']}>
                <Input
                  type="password"
                  value={formData['password']}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    updateField('password', e.target.value)
                  }
                  placeholder="••••••••"
                  invalid={!!errors['password']}
                  disabled={loading}
                  autoComplete="new-password"
                />
                <div className="mt-2 flex gap-1">
                  {[1, 2, 3, 4, 5].map((level) => (
                    <div
                      key={level}
                      className={cn(
                        'h-1 flex-1 rounded-full bg-ink/10',
                        level <= strength &&
                          (strength <= 2
                            ? 'bg-danger'
                            : strength <= 4
                              ? 'bg-warning'
                              : 'bg-success'),
                      )}
                    />
                  ))}
                </div>
                <p className="mt-1 text-xs text-ink-muted">
                  {strength <= 2 ? 'ضعیف' : strength <= 4 ? 'متوسط' : 'قوی'}
                </p>
              </Field>

              <Field label="تایید رمز عبور" error={errors['confirmPassword']}>
                <Input
                  type="password"
                  value={formData['confirmPassword']}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    updateField('confirmPassword', e.target.value)
                  }
                  placeholder="••••••••"
                  invalid={!!errors['confirmPassword']}
                  disabled={loading}
                  autoComplete="new-password"
                />
              </Field>
            </div>
          )}

          {currentStep === 1 && (
            <div className="flex flex-col gap-4">
              <Field label="نام کامل" error={errors['name']}>
                <Input
                  type="text"
                  value={formData['name']}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    updateField('name', e.target.value)
                  }
                  placeholder="علی محمدی"
                  invalid={!!errors['name']}
                  disabled={loading}
                  autoComplete="name"
                />
              </Field>
            </div>
          )}

          {currentStep === 2 && (
            <div className="flex flex-col gap-4">
              <label className="flex items-start gap-3 rounded-lg border border-ink/10 p-4">
                <Checkbox
                  checked={formData['acceptTerms']}
                  onCheckedChange={(v) => updateField('acceptTerms', Boolean(v))}
                  disabled={loading}
                />
                <div className="flex flex-col gap-1">
                  <span className="text-sm font-medium text-ink">پذیرش شرایط استفاده</span>
                  <p className="text-xs text-ink-muted">
                    با ثبت‌نام، شما با{' '}
                    <a href="#" className="text-brand-700">
                      شرایط استفاده
                    </a>{' '}
                    و{' '}
                    <a href="#" className="text-brand-700">
                      حریم خصوصی
                    </a>{' '}
                    موافقت می‌کنید.
                  </p>
                </div>
              </label>
              {errors['acceptTerms'] && (
                <p className="text-xs text-danger">{errors['acceptTerms']}</p>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between gap-3">
          {currentStep > 0 ? (
            <Button type="button" variant="secondary" onClick={handleBack} disabled={loading}>
              بازگشت
            </Button>
          ) : (
            <div />
          )}

          {currentStep < STEPS.length - 1 ? (
            <Button type="button" onClick={handleNext} disabled={loading}>
              ادامه
            </Button>
          ) : (
            <Button type="submit" loading={loading} disabled={loading}>
              ثبت‌نام
            </Button>
          )}
        </div>

        {onSignIn && (
          <p className="text-center text-sm text-ink-muted">
            قبلاً ثبت‌نام کرده‌اید؟{' '}
            <button
              type="button"
              onClick={onSignIn}
              className="font-medium text-brand-700 hover:text-brand-800"
            >
              ورود
            </button>
          </p>
        )}
      </form>
    </div>
  )
}
