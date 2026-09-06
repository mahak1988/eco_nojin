import { cn } from '@eco/utils'
import { type ReactNode, useState } from 'react'
import { Stepper } from '../primitives'
import { Button } from '../primitives'

export type FormWizardStep = {
  title: string
  description?: string
  content: ReactNode
}

export type FormWizardProps = {
  steps: FormWizardStep[]
  onComplete?: (values: Record<string, unknown>) => void
  className?: string
}

export function FormWizard({ steps, onComplete, className }: FormWizardProps) {
  const [current, setCurrent] = useState(0)
  const [values, _setValues] = useState<Record<string, unknown>>({})

  const next = () => setCurrent((c) => Math.min(steps.length - 1, c + 1))
  const prev = () => setCurrent((c) => Math.max(0, c - 1))

  const handleComplete = () => {
    onComplete?.(values)
  }

  return (
    <div className={cn('flex flex-col gap-6', className)}>
      <Stepper
        steps={steps.map((s) => ({ label: s.title, description: s.description }))}
        currentStep={current}
      />
      <div className="rounded-lg border border-ink/10 bg-surface-raised p-6">
        <div className="flex flex-col gap-4">{steps[current]?.content}</div>
      </div>
      <div className="flex items-center justify-between">
        <Button variant="secondary" onClick={prev} disabled={current === 0}>
          قبلی
        </Button>
        {current < steps.length - 1 ? (
          <Button onClick={next}>بعدی</Button>
        ) : (
          <Button onClick={handleComplete}>تکمیل</Button>
        )}
      </div>
    </div>
  )
}
