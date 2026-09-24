import { cn } from './cn';
import { forwardRef } from 'react';
import { ChevronRight, Home } from 'lucide-react';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumb({ items, className }: BreadcrumbProps) {
  return (
    <nav aria-label="Breadcrumb" className={cn('flex items-center gap-1.5 text-sm', className)}>
      <ol className="flex items-center gap-1.5">
        <li>
          <a href="/" className="flex items-center gap-1 text-ink-soft hover:text-ink">
            <Home className="h-4 w-4" aria-hidden="true" />
            <span className="sr-only">خانه</span>
          </a>
        </li>
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-1.5">
            <ChevronRight className="h-4 w-4 text-ink-faint" aria-hidden="true" />
            {item.href ? (
              <a href={item.href} className="text-ink-soft hover:text-ink">
                {item.label}
              </a>
            ) : (
              <span className="text-ink" aria-current="page">
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}