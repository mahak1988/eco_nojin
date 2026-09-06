import { cn } from '@eco/utils'
import { forwardRef, useState } from 'react'

export type ColorPickerProps = Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  'value' | 'onChange'
> & {
  value?: string
  onChange?: (value: string) => void
}

export const ColorPicker = forwardRef<HTMLDivElement, ColorPickerProps>(function ColorPicker(
  { value = '#16a34a', onChange, className, ...rest },
  ref,
) {
  const [open, setOpen] = useState(false)
  const presets = [
    '#16a34a',
    '#0ea5e9',
    '#f59e0b',
    '#ef4444',
    '#8b5cf6',
    '#3b82f6',
    '#6b7280',
    '#000000',
  ]

  return (
    <div ref={ref} className={cn('relative inline-flex', className)} {...rest}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-ink/15"
        style={{ backgroundColor: value }}
        aria-label="Pick color"
      />
      {open && (
        <div className="absolute top-full z-50 mt-2 flex rounded-lg border border-ink/10 bg-surface-raised p-2 shadow-raised">
          <div className="grid grid-cols-4 gap-2">
            {presets.map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => {
                  onChange?.(c)
                  setOpen(false)
                }}
                className="h-6 w-6 rounded-md border border-ink/10"
                style={{ backgroundColor: c }}
              />
            ))}
          </div>
          <input
            type="color"
            value={value}
            onChange={(e) => onChange?.((e.target as HTMLInputElement).value)}
            className="ms-2 h-8 w-8 cursor-pointer rounded-md border-0 bg-transparent p-0"
          />
        </div>
      )}
    </div>
  )
})
