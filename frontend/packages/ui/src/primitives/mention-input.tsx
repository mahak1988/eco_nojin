import { cn } from '@eco/utils'
import { forwardRef, useState } from 'react'

export type MentionInputProps = Omit<
  React.TextareaHTMLAttributes<HTMLTextAreaElement>,
  'value' | 'onChange'
> & {
  value: string
  onChange: (value: string) => void
  mentions: string[]
}

export const MentionInput = forwardRef<HTMLTextAreaElement, MentionInputProps>(
  function MentionInput({ value, onChange, mentions, className, ...rest }, ref) {
    const [showSuggestions, setShowSuggestions] = useState(false)
    const [query, setQuery] = useState('')

    const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const text = e.target.value
      onChange(text)
      const lastChar = text.slice(-1)
      if (lastChar === '@') {
        setShowSuggestions(true)
        setQuery('')
      } else if (showSuggestions) {
        const match = text.match(/@(\w*)$/)
        setQuery(match?.[1] ?? '')
      }
    }

    const insertMention = (name: string) => {
      const base = value.replace(/@\w*$/, '')
      onChange(`${base}@${name} `)
      setShowSuggestions(false)
    }

    const filtered = mentions.filter((m) => m.includes(query))

    return (
      <div className={cn('relative', className)}>
        <textarea
          ref={ref}
          value={value}
          onChange={handleChange}
          className={cn(
            'block w-full rounded-md border border-ink/15 bg-surface-raised px-3 py-2 text-sm text-ink',
            'placeholder:text-ink-subtle focus:outline-none focus:shadow-glow focus:border-brand-500',
            'disabled:cursor-not-allowed disabled:bg-surface-muted',
          )}
          {...rest}
        />
        {showSuggestions && filtered.length > 0 && (
          <div className="absolute z-50 mt-1 max-h-40 w-full overflow-auto rounded-md border border-ink/10 bg-surface-raised shadow-raised">
            {filtered.map((name) => (
              <button
                key={name}
                type="button"
                onClick={() => insertMention(name)}
                className="block w-full px-3 py-2 text-right text-sm hover:bg-surface-muted"
              >
                @{name}
              </button>
            ))}
          </div>
        )}
      </div>
    )
  },
)
