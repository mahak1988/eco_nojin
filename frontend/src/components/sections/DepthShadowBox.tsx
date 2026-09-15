import { cn } from '../../lib/utils';

/** Container with layered depth shadows. */
export default function DepthShadowBox({
  children,
  className,
  depth = 1,
}: {
  children: React.ReactNode;
  className?: string;
  depth?: 1 | 2 | 3;
}) {
  const shadows = [
    '0 4px 6px rgba(0,0,0,0.1)',
    '0 10px 20px rgba(0,0,0,0.15), 0 3px 6px rgba(0,0,0,0.1)',
    '0 20px 40px rgba(0,0,0,0.25), 0 8px 16px rgba(0,0,0,0.15)',
  ];

  return (
    <div
      className={cn('rounded-3xl glass p-6', className)}
      style={{ boxShadow: shadows[depth - 1] }}
    >
      {children}
    </div>
  );
}
