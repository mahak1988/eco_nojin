import { cn } from './cn';

export interface StepperStep {
  id: string;
  label: string;
  description?: string;
}

export function Stepper({
  steps,
  current,
  className,
}: {
  steps: StepperStep[];
  current: string;
  className?: string;
}) {
  const currentIndex = Math.max(
    steps.findIndex((step) => step.id === current),
    0,
  );
  return (
    <ol className={cn('flex w-full flex-col gap-2', className)} aria-label="Progress">
      {steps.map((step, index) => {
        const state =
          index < currentIndex ? 'complete' : index === currentIndex ? 'current' : 'upcoming';
        return (
          <li
            key={step.id}
            aria-current={state === 'current' ? 'step' : undefined}
            className="flex gap-3"
          >
            <span
              className={cn(
                'flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold',
                state === 'complete' && 'bg-forest text-on-action',
                state === 'current' && 'border-2 border-forest text-forest',
                state === 'upcoming' && 'border border-line text-ink-soft',
              )}
            >
              {index + 1}
            </span>
            <span>
              <span className="block text-sm font-medium text-ink">{step.label}</span>
              {step.description && (
                <span className="block text-xs text-ink-soft">{step.description}</span>
              )}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
