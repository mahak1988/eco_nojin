import type { Preview } from '@storybook/react-vite';

// The production stylesheet, not a Storybook approximation of it: the `@theme`
// block, the fourteen `@font-face` families, the spacing and radius steps and
// every `light-dark()` pair come from the file the app itself serves. The Vite
// builder runs it through the same `@tailwindcss/postcss` plugin `next.config`
// uses, so a utility that resolves in the app resolves here too — and the
// `check-colour-utilities.mjs` gate is what keeps the two in step.
import '../src/app/globals.css';
import './preview.css';

import { globalTypes, withDocumentLocale } from './ds-context';

const preview: Preview = {
  parameters: {
    controls: {
      matchers: { color: /(background|color)$/i, date: /Date$/i },
    },
    a11y: {
      // `error` turns a violation from a yellow highlight in the panel into a
      // failed test, which is the only form of this that can be a gate.
      test: 'error',
      config: {
        rules: [
          /**
           * A story is a component, not a document: no `<main>`, no `<h1>`, no
           * landmark structure, because a component library is not responsible
           * for the page around it. The same four rules are excluded in
           * `visual/specs/design-system.spec.ts`, where axe runs as the gate.
           *
           * `color-contrast` is deliberately not among them — it is the rule a
           * token-driven palette lives or dies by.
           */
          { id: 'region', enabled: false },
          { id: 'landmark-one-main', enabled: false },
          { id: 'landmark-unique', enabled: false },
          { id: 'page-has-heading-one', enabled: false },
          { id: 'bypass', enabled: false },
          { id: 'color-contrast', enabled: true },
        ],
      },
    },
    options: {
      storySort: { order: ['Primitives', 'Data', 'Navigation', 'Surfaces'] },
    },
  },
  globalTypes,
  decorators: [withDocumentLocale],
};

export default preview;
