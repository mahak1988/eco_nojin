import { cn } from '@eco/utils'
import { useEffect, useRef, useState } from 'react'
import { Button } from '../../primitives'
import { Field } from '../../primitives'
import { OTPInput } from '../../primitives'
import { Countdown } from '../../primitives'
import { validateField, validators } from '../../utils/validators'
import { AlertBanner } from '../alert-banner'

export type TwoFactorFormProps = {
  onSubmit: (code: string) => Promise<void> | void
  onBack?: () => void
  onUseBackupCode?: () => void
  resendTimer?: number
  className?: string
}

export function TwoFactorForm({
  onSubmit,
  onBack,
  onUseBackupCode,
  resendTimer = 30,
  className,
}: TwoFactorFormProps) {
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [canResend, setCanResend] = useState(false)
  const [timeLeft, setTimeLeft] = useState(resendTimer)
  const inputRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (timeLeft <= 0) {
      setCanResend(true)
      return
    }
    const id = setInterval(() => setTimeLeft((t) => t - 1), 1000)
    return () => clearInterval(id)
  }, [timeLeft])

  useEffect(() => {
    const timer = setTimeout(() => inputRef.current?.querySelector('input')?.focus(), 100)
    return () => clearTimeout(timer)
  }, [])

  const handleSubmit = async () => {
    setError(null)
    const validationError = validateField(code, [
      { validator: validators.otp('کد باید ۶ رقم باشد') },
    ])
    if (validationError) {
      setError(validationError)
      return
    }

    setLoading(true)
    try {
      await onSubmit(code)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'کد وارد شده نامعتبر است.')
      setCode('')
    } finally {
      setLoading(false)
    }
  }

  const handleResend = () => {
    setTimeLeft(resendTimer)
    setCanResend(false)
    setCode('')
    setError(null)
  }

  return (
    <div className={cn('w-full', className)}>
      <div className="mb-6 text-center">
        <h2 className="text-xl font-bold text-ink">احراز دو مرحله‌ای</h2>
        <p className="mt-1 text-sm text-ink-muted">کد ۶ رقمی ارسال شده به تلفن خود را وارد کنید</p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          handleSubmit()
        }}
        className="flex flex-col gap-5"
        noValidate
      >
        {error && <AlertBanner tone="danger">{error}</AlertBanner>}

        <Field label="کد تایید" error={error}>
          <div ref={inputRef}>
            <OTPInput value={code} onChange={setCode} length={6} disabled={loading} />
          </div>
        </Field>

        <div className="flex items-center justify-between text-sm">
          <span className="text-ink-muted">
            {canResend ? (
              <button
                type="button"
                onClick={handleResend}
                className="font-medium text-brand-700 hover:text-brand-800"
              >
                ارسال مجدد کد
              </button>
            ) : (
              <span>
                ارسال مجدد در <Countdown target={Date.now() + timeLeft * 1000} />
              </span>
            )}
          </span>
        </div>

        <Button type="submit" fullWidth loading={loading} disabled={loading || code.length !== 6}>
          تایید
        </Button>

        <div className="flex items-center justify-between">
          {onBack && (
            <Button type="button" variant="ghost" onClick={onBack} disabled={loading}>
              بازگشت
            </Button>
          )}
          {onUseBackupCode && (
            <Button
              type="button"
              variant="ghost"
              onClick={onUseBackupCode}
              disabled={loading}
              className="ms-auto"
            >
              استفاده از کد پشتیبان
            </Button>
          )}
        </div>
      </form>
    </div>
  )
}
