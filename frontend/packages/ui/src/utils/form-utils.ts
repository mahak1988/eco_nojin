export type FormFieldProps = {
  label: string
  name: string
  value: string
  onChange: (value: string) => void
  onBlur?: () => void
  error?: string
  hint?: string
  type?: string
  placeholder?: string
  disabled?: boolean
  autoComplete?: string
  inputMode?: 'text' | 'email' | 'numeric' | 'tel' | 'url'
  autoFocus?: boolean
  maxLength?: number
}
