import { cn } from '@eco/utils'
import { useRef } from 'react'

export type RichTextEditorProps = {
  value: string
  onChange: (html: string) => void
  className?: string
  placeholder?: string
}

export function RichTextEditor({
  value,
  onChange,
  className,
  placeholder = 'متن را اینجا بنویسید...',
}: RichTextEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null)

  const exec = (command: string, arg?: string) => {
    document.execCommand(command, false, arg)
    editorRef.current?.focus()
    sync()
  }

  const sync = () => {
    if (editorRef.current) onChange(editorRef.current.innerHTML)
  }

  const ToolbarButton = ({
    command,
    label,
    arg,
  }: { command: string; label: string; arg?: string }) => (
    <button
      type="button"
      onMouseDown={(e) => {
        e.preventDefault()
        exec(command, arg)
      }}
      className="rounded px-2 py-1 text-xs hover:bg-surface-muted"
    >
      {label}
    </button>
  )

  return (
    <div className={cn('rounded-lg border border-ink/10 bg-surface-raised', className)}>
      <div className="flex flex-wrap items-center gap-1 border-b border-ink/10 p-2">
        <ToolbarButton command="bold" label="B" />
        <ToolbarButton command="italic" label="I" />
        <ToolbarButton command="underline" label="U" />
        <ToolbarButton command="strikeThrough" label="S" />
        <ToolbarButton command="insertUnorderedList" label="• List" />
        <ToolbarButton command="insertOrderedList" label="1. List" />
        <ToolbarButton command="justifyLeft" label="Left" />
        <ToolbarButton command="justifyCenter" label="Center" />
        <ToolbarButton command="justifyRight" label="Right" />
      </div>
      <div
        ref={editorRef}
        contentEditable
        suppressContentEditableWarning
        onInput={sync}
        onBlur={sync}
        dangerouslySetInnerHTML={{ __html: value }}
        className="min-h-[120px] p-3 text-sm text-ink outline-none"
        data-placeholder={placeholder}
      />
      <style>{`
        [contenteditable][data-placeholder]:empty:before {
          content: attr(data-placeholder);
          color: rgb(var(--color-ink-subtle));
        }
      `}</style>
    </div>
  )
}
