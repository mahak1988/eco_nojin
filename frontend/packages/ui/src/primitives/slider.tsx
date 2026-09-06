import { cn } from '@eco/utils'
import * as RS from '@radix-ui/react-slider'
import { forwardRef } from 'react'

export type SliderProps = Omit<RS.SliderProps, 'onValueChange'> & {
  onValueChange?: (value: number[]) => void
}

export const Slider = forwardRef<HTMLDivElement, SliderProps>(function Slider(
  { className, value = [50], onValueChange, ...rest },
  ref,
) {
  return (
    <RS.Root
      ref={ref}
      value={value}
      onValueChange={onValueChange}
      max={100}
      step={1}
      className={cn('relative flex h-5 w-full touch-none select-none items-center', className)}
      {...rest}
    >
      <RS.Track className="relative h-1.5 w-full grow rounded-full bg-ink/10">
        <RS.Range className="absolute h-full rounded-full bg-brand-600" />
      </RS.Track>
      {value.map((_v, i) => (
        <RS.Thumb
          key={i}
          className={cn(
            'block h-4 w-4 rounded-full border-2 border-brand-600 bg-white shadow-sm',
            'focus:outline-none focus:shadow-glow',
            'disabled:cursor-not-allowed disabled:opacity-50',
          )}
        />
      ))}
    </RS.Root>
  )
})
