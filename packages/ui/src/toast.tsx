import { Toaster as SonnerToaster, toast } from 'sonner';

type ToasterProps = {
  className?: string;
};

export const Toaster = ({ className }: ToasterProps) => (
  <SonnerToaster
    className={className}
    theme="system"
    toastOptions={{
      classNames: {
        toast: 'group rounded-lg bg-surface text-foreground shadow-lg ring-1 ring-border p-4',
        description: 'text-sm text-muted',
        actionButton: 'rounded-md bg-primary px-3 py-1 text-sm font-medium text-primary-foreground hover:bg-primary/90',
        cancelButton: 'rounded-md bg-muted px-3 py-1 text-sm font-medium text-foreground hover:bg-muted/80',
        closeButton: 'text-muted hover:text-foreground',
      },
    }}
  />
);

export { toast };
export { toast as toastPromise } from 'sonner';