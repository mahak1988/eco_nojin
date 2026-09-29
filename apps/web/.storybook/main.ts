import { resolve } from 'node:path';
import type { StorybookConfig } from '@storybook/react-vite';
import tailwindcss from '@tailwindcss/postcss';
import react from '@vitejs/plugin-react';

/**
 * Storybook 9 on the same toolchain the app itself runs on.
 *
 * The one thing that must be true for this catalogue to be worth anything is
 * that the preview is styled by `src/app/globals.css` and not by a
 * Storybook-shaped approximation of it. A design system reviewed against
 * colours, spacing steps and fonts that only exist inside the harness is a
 * review of the harness. So the Tailwind 4 PostCSS plugin the app uses is
 * wired in here by name, and `preview.tsx` imports the production stylesheet
 * itself; the `@theme` block, the fourteen `@font-face` families and the
 * `light-dark()` pairs are then the same declarations the app serves.
 */
/**
 * Storybook loads this file through `esbuild-register` as CommonJS, so the path
 * has to come from `__dirname`. `import.meta.dirname` compiles to `undefined`
 * here and the config dies before it is read.
 */
const APP_DIR = resolve(__dirname, '..');

const config: StorybookConfig = {
  framework: { name: '@storybook/react-vite', options: {} },
  // Only the design-system component directories. A story in `templates/` or in
  // a route would drag Next's server runtime into a Vite preview; the primitives
  // are the part of the tree a component library is responsible for.
  stories: [
    '../src/components/ui/**/*.stories.@(ts|tsx)',
    '../src/components/surface/**/*.stories.@(ts|tsx)',
  ],
  addons: ['@storybook/addon-a11y'],
  /**
   * The seven bundled families are declared with absolute `url("/fonts/…")`
   * sources, exactly as they are in production, so they only resolve if the
   * application's `public/` is mounted at the preview root. This is the same
   * `fonts/vazirmatn-latin-400-normal-*.woff2` request the browser makes in the
   * app — nothing is fetched from a third-party origin and no metric is faked.
   */
  staticDirs: ['../public'],
  core: { disableTelemetry: true },
  typescript: {
    /**
     * Storydocgen is off on purpose. The extractor parses each story with esbuild
     * configured for the `.ts` loader rather than `.tsx`, so any story containing
     * JSX fails to parse before Vite ever sees it — and every story contains JSX.
     * Arg types here are declared in the story itself, which is where a
     * design-system catalogue wants them to be reviewed anyway.
     */
    reactDocgen: false,
  },
  viteFinal: async (viteConfig) => ({
    ...viteConfig,
    /**
     * The React plugin is added by hand rather than left to the framework preset.
     *
     * Vite 8 is built on Rolldown and only transforms JSX when a plugin claims the
     * file, so a preview without `@vitejs/plugin-react` does not silently fall back
     * to untransformed JSX — it fails to parse, and Storybook's own
     * `inject-export-order-plugin` then fails on the raw source as well. The
     * version here is the one already in the tree and the one `vitest.config.ts`
     * uses, so the story files and the unit tests are transformed by the same
     * plugin at the same settings.
     */
    plugins: [...(viteConfig.plugins ?? []), react()],
    resolve: {
      ...viteConfig.resolve,
      // The `@/…` specifier from `tsconfig.json`, so a component under test
      // resolves the same imports it does in the app instead of a story-only
      // copy of them.
      alias: { ...(viteConfig.resolve?.alias as object), '@': resolve(APP_DIR, 'src') },
    },
    css: {
      ...viteConfig.css,
      /**
       * Vite 8 runs CSS through Lightning CSS by default, and Lightning CSS
       * rewrites the design system's own primitive: every
       * `light-dark(a, b)` in `globals.css` comes back out as a
       * `--lightningcss-light` / `--lightningcss-dark` pair driven by
       * `prefers-color-scheme`. The result computes to the same colour, so a
       * palette reviewer would not notice — but the preview would no longer be
       * rendering the tokens the production build renders, and "the same
       * stylesheet" would be a claim rather than a fact. PostCSS is what
       * `postcss.config.mjs` gives Next, so the preview uses PostCSS too.
       */
      transformer: 'postcss',
      postcss: { plugins: [tailwindcss()] },
    },
    build: { ...viteConfig.build, cssMinify: 'esbuild' },
  }),
};

export default config;
