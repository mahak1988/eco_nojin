import { cn } from '@eco/utils'
import type { ReactNode } from 'react'
import { Card, CardBody, CardHeader } from '../primitives'

export type SettingsSectionProps = {
  title: string
  description?: string
  children: ReactNode
  className?: string
}

export function SettingsSection({ title, description, children, className }: SettingsSectionProps) {
  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader>
        <div className="flex flex-col gap-1">
          <h3 className="text-base font-semibold text-ink">{title}</h3>
          {description && <p className="text-sm text-ink-muted">{description}</p>}
        </div>
      </CardHeader>
      <CardBody>
        <div className="flex flex-col gap-4">{children}</div>
      </CardBody>
    </Card>
  )
}
