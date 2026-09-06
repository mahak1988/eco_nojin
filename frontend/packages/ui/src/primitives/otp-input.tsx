import { cn } from '@eco/utils'
import { forwardRef, useRef } from 'react'

export type OTPInputProps = Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  'value' | 'onChange'
> & {
  value: string
  onChange: (value: string) => void
  length?: number
}

export const OTPInput = forwardRef<HTMLDivElement, OTPInputProps>(function OTPInput(
  { value, onChange, length = 6, className, ...rest },
  ref,
) {
  const inputsRef = useRef<(HTMLInputElement | null)[]>([])

  const handleChange = (index: number, char: string) => {
    if (!/^\d*$/.test(char)) return
    const newValue = value.split('')
    newValue[index] = char.slice(-1)
    const next = newValue.join('').slice(0, length)
    onChange(next)
    if (char && index < length - 1) {
      inputsRef.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !value[index] && index > 0) {
      inputsRef.current[index - 1]?.focus()
    }
  }

  return (
    <div ref={ref} className={cn('flex items-center gap-2', className)} {...rest}>
      {Array.from({ length }, (_, i) => (
        <input
          key={i}
          ref={(el) => {
            inputsRef.current[i] = el
          }}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={value[i] ?? ''}
          onChange={(e) => handleChange(i, e.target.value)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          className="h-11 w-11 rounded-md border border-ink/15 bg-surface-raised text-center text-lg font-semibold text-ink focus:outline-none focus:shadow-glow focus:border-brand-500"
          aria-label={`Digit ${i + 1}`}
        />
      ))}
    </div>
  )
})
