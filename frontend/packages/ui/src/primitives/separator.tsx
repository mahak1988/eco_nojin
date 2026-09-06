import { cn } from '@eco/utils'
import * as RS from '@radix-ui/react-separator'
import { forwardRef } from 'react'

export const Separator = forwardRef<HTMLDivElement, React.ComponentPropsWithoutRef<typeof RS.Root>>(
  function Separator({ className, decorative = true, orientation = 'horizontal', ...rest }, ref) {
    return (
      <RS.Root
        ref={ref}
        decorative={decorative}
        orientation={orientation}
        className={cn(
          'shrink-0 bg-ink/10',
          orientation === 'horizontal' ? 'h-px w-full' : 'h-full w-px',
          className,
        )}
        {...rest}
      />
    )
  },
)
