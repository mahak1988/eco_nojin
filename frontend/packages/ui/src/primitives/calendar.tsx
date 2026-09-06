import { cn } from '@eco/utils'
import type { HTMLAttributes } from 'react'
import { ChevronLeft, ChevronRight } from './icon'

const WEEK_DAYS = ['ش', 'ی', 'د', 'س', 'چ', 'پ', 'ج']

function getDaysInMonth(year: number, month: number) {
  return new Date(year, month + 1, 0).getDate()
}

function getFirstDayOfMonth(year: number, month: number) {
  return new Date(year, month, 1).getDay()
}

export type CalendarProps = HTMLAttributes<HTMLDivElement> & {
  value?: Date
  onChange?: (date: Date) => void
}

export function Calendar({ value, onChange, className, ...rest }: CalendarProps) {
  const today = new Date()
  const currentYear = value?.getFullYear() ?? today.getFullYear()
  const currentMonth = value?.getMonth() ?? today.getMonth()
  const selectedDate = value ? new Date(currentYear, currentMonth, value.getDate()) : null

  const daysInMonth = getDaysInMonth(currentYear, currentMonth)
  const firstDay = getFirstDayOfMonth(currentYear, currentMonth)

  const prevMonth = () => {
    const d = new Date(currentYear, currentMonth - 1, 1)
    onChange?.(d)
  }
  const nextMonth = () => {
    const d = new Date(currentYear, currentMonth + 1, 1)
    onChange?.(d)
  }

  const days = []
  for (let i = 0; i < firstDay; i++) days.push(null)
  for (let i = 1; i <= daysInMonth; i++) days.push(i)

  return (
    <div
      className={cn('w-full rounded-lg border border-ink/10 bg-surface-raised p-3', className)}
      {...rest}
    >
      <div className="mb-3 flex items-center justify-between">
        <button
          type="button"
          onClick={prevMonth}
          className="rounded p-1 hover:bg-surface-muted"
          aria-label="Previous month"
        >
          <ChevronRight size={16} />
        </button>
        <span className="text-sm font-semibold">
          {new Date(currentYear, currentMonth).toLocaleDateString('fa-IR', {
            month: 'long',
            year: 'numeric',
          })}
        </span>
        <button
          type="button"
          onClick={nextMonth}
          className="rounded p-1 hover:bg-surface-muted"
          aria-label="Next month"
        >
          <ChevronLeft size={16} />
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-xs text-ink-muted">
        {WEEK_DAYS.map((d) => (
          <div key={d} className="py-1">
            {d}
          </div>
        ))}
        {days.map((day, i) => (
          <button
            key={i}
            type="button"
            disabled={!day}
            onClick={() => day && onChange?.(new Date(currentYear, currentMonth, day))}
            className={cn(
              'h-8 w-8 rounded-md text-sm',
              day && 'hover:bg-surface-muted',
              selectedDate &&
                day === selectedDate.getDate() &&
                !selectedDate.getDate() &&
                'bg-brand-600 text-white',
              selectedDate && day === selectedDate.getDate() && 'bg-brand-600 text-white',
            )}
          >
            {day ?? ''}
          </button>
        ))}
      </div>
    </div>
  )
}
