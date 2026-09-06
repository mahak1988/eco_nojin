import { cn } from '@eco/utils'
import { type ReactNode, useState } from 'react'
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  NavigationMenuViewport,
} from '../primitives/navigation-menu'

export type MegaMenuItem = {
  title: string
  href?: string
  description?: string
  icon?: ReactNode
}

export type MegaMenuProps = {
  items: { title: string; links: MegaMenuItem[] }[]
  className?: string
}

export function MegaMenu({ items, className }: MegaMenuProps) {
  const [_open, _setOpen] = useState(false)
  return (
    <NavigationMenu className={cn('max-w-none', className)}>
      <NavigationMenuList className="gap-1">
        {items.map((group) => (
          <NavigationMenuItem key={group.title}>
            <NavigationMenuTrigger>{group.title}</NavigationMenuTrigger>
            <NavigationMenuContent>
              <ul className="grid gap-2 p-2 md:w-[400px] md:grid-cols-2">
                {group.links.map((link) => (
                  <li key={link.title}>
                    <NavigationMenuLink
                      href={link.href ?? '#'}
                      className="flex flex-col gap-1 rounded-md p-2"
                    >
                      {link.icon && <span className="text-ink-subtle">{link.icon}</span>}
                      <span className="text-sm font-medium text-ink">{link.title}</span>
                      {link.description && (
                        <span className="text-xs text-ink-muted">{link.description}</span>
                      )}
                    </NavigationMenuLink>
                  </li>
                ))}
              </ul>
            </NavigationMenuContent>
          </NavigationMenuItem>
        ))}
      </NavigationMenuList>
      <NavigationMenuViewport />
    </NavigationMenu>
  )
}
