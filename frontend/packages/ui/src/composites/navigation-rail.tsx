import { type ReactNode } from 'react';
import { cn } from '@eco/utils';
import { Tooltip, TooltipContent, TooltipTrigger } from '../composites/tooltip';

export type NavigationRailItem = {
  id: string;
  label: string;
  icon: ReactNode;
  badge?: number;
  onClick?: () => void;
};

export type NavigationRailProps = {
  items: NavigationRailItem[];
  activeItem?: string;
  collapsed?: boolean;
  onNavigate?: (id: string) => void;
  className?: string;
};

export function NavigationRail({ items, activeItem, collapsed = false, onNavigate, className }: NavigationRailProps) {
  return (
    <nav
      className={cn(
        'flex h-full flex-col items-center gap-1 border-e border-ink/10 bg-surface-inverse px-2 py-4 text-ink-inverse',
        collapsed ? 'w-16' : 'w-64',
        className,
      )}
      aria-label="ناوبری جانبی"
    >
      {items.map((item) => {
        const isActive = activeItem === item.id;
        const button = (
          <button
            key={item.id}
            type="button"
            onClick={() => onNavigate?.(item.id) ?? item.onClick?.()}
            className={cn(
              'relative flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-colors',
              isActive ? 'bg-surface-raised/10 text-white' : 'text-ink-inverse/80 hover:bg-surface-raised/5 hover:text-white',
              collapsed && 'justify-center px-0',
            )}
            aria-current={isActive ? 'page' : undefined}
          >
            <span className={cn('shrink-0', !collapsed && 'text-lg')} aria-hidden="true">
              {item.icon}
            </span>
            {!collapsed && (
              <span className="truncate font-medium">{item.label}</span>
            )}
            {item.badge != null && item.badge > 0 && (
              <span className="absolute -top-1 -end-1 flex h-5 w-5 items-center justify-center rounded-full bg-danger text-[10px] font-bold text-white">
                {item.badge}
              </span>
            )}
          </button>
        );

        if (collapsed) {
          return (
            <Tooltip key={item.id}>
              <TooltipTrigger asChild>
                {button}
              </TooltipTrigger>
              <TooltipContent side="left">
                <p>{item.label}</p>
              </TooltipContent>
            </Tooltip>
          );
        }

        return button;
      })}
    </nav>
  );
}
