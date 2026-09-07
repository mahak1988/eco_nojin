import { Suspense, lazy, type ComponentType, type ReactElement } from 'react';
import { Spinner } from '@eco/ui';

/**
 * Route-level code-splitting helper.
 * Supports default exports, explicit named exports, and auto-detection
 * (prefers an export ending in "Page", else the first PascalCase function).
 */
export function lazyPage(
  load: () => Promise<Record<string, unknown>>,
  named?: string,
): () => ReactElement {
  const C = lazy(async () => {
    const mod = await load();

    let comp: unknown = named ? mod[named] : mod['default'];

    if (typeof comp !== 'function' && !named) {
      const candidates = Object.keys(mod).filter(
        (k) => k !== 'default' && /^[A-Z]/.test(k) && typeof mod[k] === 'function',
      );
      const pick = candidates.find((k) => k.endsWith('Page')) ?? candidates[0];
      comp = pick ? mod[pick] : undefined;
    }

    if (typeof comp !== 'function') {
      throw new Error(
        named
          ? 'lazyPage: export "' + named + '" not found in module'
          : 'lazyPage: no default export and no component-like export found',
      );
    }

    return { default: comp as ComponentType };
  });

  function LazyRoute(): ReactElement {
    return (
      <Suspense
        fallback={
          <div className="flex min-h-[60vh] items-center justify-center">
            <Spinner size="lg" />
          </div>
        }
      >
        <C />
      </Suspense>
    );
  }

  return LazyRoute;
}
