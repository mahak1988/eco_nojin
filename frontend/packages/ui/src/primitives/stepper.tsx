import { cn } from '@eco/utils'
import type { HTMLAttributes, ReactNode } from 'react'
import { Check } from './icon'

export type StepItem = {
  label: string
  description?: string
  icon?: ReactNode
}

export type StepperProps = HTMLAttributes<HTMLElement> & {
  steps: StepItem[]
  currentStep: number
  onStepClick?: (step: number) => void
}

export function Stepper({ steps, currentStep, onStepClick, className, ...rest }: StepperProps) {
  return (
    <nav aria-label="Progress" className={cn('w-full', className)} {...rest}>
      <ol className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep
          const isCurrent = index === currentStep
          return (
            <li key={index} className="flex flex-1 items-center">
              <button
                type="button"
                onClick={() => onStepClick?.(index)}
                disabled={!onStepClick}
                className={cn('flex items-center gap-2 text-sm', onStepClick && 'cursor-pointer')}
              >
                <span
                  className={cn(
                    'flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-bold transition-colors',
                    isCompleted && 'border-brand-600 bg-brand-600 text-white',
                    isCurrent && 'border-brand-600 text-brand-700',
                    !isCompleted && !isCurrent && 'border-ink/20 text-ink-muted',
                  )}
                >
                  {isCompleted ? <Check size={14} /> : (step.icon ?? index + 1)}
                </span>
                <span
                  className={cn(
                    'hidden text-sm font-medium sm:block',
                    isCurrent && 'text-ink',
                    !isCurrent && 'text-ink-muted',
                  )}
                >
                  {step.label}
                </span>
              </button>
              {index < steps.length - 1 && (
                <div className={cn('mx-2 h-0.5 flex-1 bg-ink/10', isCompleted && 'bg-brand-600')} />
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
