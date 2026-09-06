/**
 * Tailwind plugin: register semantic typography utilities.
 *
 * Adds `.text-display`, `.text-h1`, `.text-h2`, …  and their responsive variants.
 * Source: packages/ui/src/tokens/typography.ts.
 */
import plugin from 'tailwindcss/plugin';

import { roleClasses } from '@eco/ui/tokens/typography';

export default plugin(({ addUtilities }) => {
  const utilities: Record<string, Record<string, string>> = {};
  for (const [role, classes] of Object.entries(roleClasses)) {
    utilities[`.text-${role}`] = classes
      .split(/\s+/)
      .reduce<Record<string, string>>((acc, cls) => {
        if (cls.startsWith('text-') || cls.startsWith('font-') || cls.startsWith('leading-') || cls.startsWith('tracking-') || cls.startsWith('uppercase')) {
          acc[cls] = cls;
        }
        return acc;
      }, {});
  }
  addUtilities(utilities);
});