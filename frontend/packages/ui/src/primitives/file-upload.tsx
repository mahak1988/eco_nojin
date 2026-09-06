import { cn } from '@eco/utils'
import type { ChangeEvent, DragEvent, HTMLAttributes } from 'react'
import { useState } from 'react'
import { UploadCloud } from '../primitives/icon'

export type FileUploadProps = HTMLAttributes<HTMLDivElement> & {
  accept?: string
  multiple?: boolean
  maxFiles?: number
  onFiles?: (files: File[]) => void
}

export function FileUpload({
  accept,
  multiple = false,
  maxFiles = 1,
  onFiles,
  className,
  ...rest
}: FileUploadProps) {
  const [dragOver, setDragOver] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFiles = (files: FileList | null) => {
    if (!files) return
    const list = Array.from(files) as File[]
    if (list.length > maxFiles) {
      setError(`حداکثر ${maxFiles} فایل مجاز است.`)
      return
    }
    setError(null)
    onFiles?.(list)
  }

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragOver(false)
    handleFiles(e.dataTransfer.files as unknown as FileList)
  }

  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    handleFiles(e.target.files)
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
      className={cn(
        'flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-ink/20 bg-surface-muted p-6 text-center transition-colors',
        dragOver && 'border-brand-500 bg-brand-50/50',
        className,
      )}
      {...rest}
    >
      <UploadCloud size={28} className="text-ink-subtle" />
      <p className="text-sm font-medium text-ink">فایل را اینجا رها کنید یا کلیک کنید</p>
      <p className="text-xs text-ink-muted">PNG, JPG, PDF تا حداکثر ۱۰ مگابایت</p>
      <input
        type="file"
        accept={accept}
        multiple={multiple}
        onChange={onChange}
        className="sr-only"
        id="file-upload-input"
      />
      <label
        htmlFor="file-upload-input"
        className="cursor-pointer rounded-md bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700"
      >
        انتخاب فایل
      </label>
      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  )
}
