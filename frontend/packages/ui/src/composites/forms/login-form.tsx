import { cn } from '@eco/utils'
import { type ChangeEvent, type FormEvent, useState } from 'react'
import { Button } from '../../primitives'
import { Field } from '../../primitives'
import { Input } from '../../primitives'
import { Checkbox } from '../../primitives'
import { type ValidationRule, validateField, validators } from '../../utils/validators'
import { AlertBanner } from '../alert-banner'

export type LoginFormProps = {
  onSubmit: (credentials: {
    email: string
    password: string
    remember: boolean
  }) => Promise<void> | void
  onForgotPassword?: () => void
  onSignUp?: () => void
  className?: string
}

const RULES: Record<string, ValidationRule[]> = {
  email: [
    { validator: validators.required('ایمیل الزامی است') },
    { validator: validators.email('ایمیل نامعتبر است') },
  ],
  password: [
    { validator: validators.required('رمز عبور الزامی است') },
    { validator: validators.password('رمز عبور باید حداقل ۸ کاراکتر باشد') },
  ],
}

export function LoginForm({ onSubmit, onForgotPassword, onSignUp, className }: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [remember, setRemember] = useState(false)
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const validate = (field: string, value: string) => {
    const rules = RULES[field]
    if (!rules) return undefined
    return validateField(value, rules)
  }

  const handleBlur = (field: string) => {
    const value = field === 'email' ? email : password
    const error = validate(field, value)
    setErrors((prev) => ({ ...prev, [field]: error ?? '' }))
  }

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setServerError(null)

    const emailError = validate('email', email)
    const passwordError = validate('password', password)
    const newErrors = { email: emailError ?? '', password: passwordError ?? '' }

    if (emailError || passwordError) {
      setErrors(newErrors)
      return
    }

    setLoading(true)
    try {
      await onSubmit({ email, password, remember })
    } catch (err) {
      setServerError(err instanceof Error ? err.message : 'خطا در ورود. لطفاً دوباره تلاش کنید.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={cn('w-full', className)}>
      <form onSubmit={handleSubmit} className="flex flex-col gap-5" noValidate>
        {serverError && <AlertBanner tone="danger">{serverError}</AlertBanner>}

        <Field label="ایمیل" error={errors['email']}>
          <Input
            type="email"
            value={email}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
            onBlur={() => handleBlur('email')}
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
            value={password}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
            onBlur={() => handleBlur('password')}
            placeholder="••••••••"
            invalid={!!errors['password']}
            disabled={loading}
            autoComplete="current-password"
          />
        </Field>

        <div className="flex items-center justify-between">
          <label className="flex items-center gap-2 text-sm text-ink">
            <Checkbox checked={remember} onCheckedChange={(v) => setRemember(Boolean(v))} />
            <span>مرا به خاطر بسپار</span>
          </label>
          {onForgotPassword && (
            <button
              type="button"
              onClick={onForgotPassword}
              className="text-sm font-medium text-brand-700 hover:text-brand-800"
            >
              فراموشی رمز؟
            </button>
          )}
        </div>

        <Button type="submit" fullWidth loading={loading} disabled={loading}>
          ورود
        </Button>

        {onSignUp && (
          <p className="text-center text-sm text-ink-muted">
            حساب ندارید؟{' '}
            <button
              type="button"
              onClick={onSignUp}
              className="font-medium text-brand-700 hover:text-brand-800"
            >
              ثبت‌نام
            </button>
          </p>
        )}
      </form>
    </div>
  )
}
