// Thin re-export — the canonical brand lives in @eco/ui.
export { BrandWordmark } from '@eco/ui';
import { LogoMark } from '@eco/ui';

export function BrandMark({
  size = 32,
  className,
}: {
  size?: number;
  className?: string;
}) {
  return <LogoMark size={size} className={className} />;
}
