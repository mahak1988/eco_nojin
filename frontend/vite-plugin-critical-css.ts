import type { Plugin } from 'vite';

/**
 * Vite plugin to inline critical CSS for above-the-fold content.
 * Extracts critical styles and injects them into the HTML head.
 */
export function criticalCSSInline(): Plugin {
  let criticalCSS = '';
  let isProduction = false;

  return {
    name: 'vite-plugin-critical-css',
    enforce: 'post',
    configResolved(config) {
      isProduction = config.command === 'build';
    },
    async buildStart() {
      if (!isProduction) return;
      
      // Read the built CSS file to extract critical rules
      // We'll define critical CSS patterns for above-the-fold content
      criticalCSS = `
        /* Critical CSS - Above the fold */
        *, *::before, *::after { box-sizing: border-box; }
        html { scroll-behavior: smooth; }
        body { 
          background-color: var(--color-night-950); 
          color: var(--color-night-100); 
          font-family: var(--font-sans); 
          -webkit-font-smoothing: antialiased; 
          text-rendering: optimizeLegibility; 
          overflow-x: hidden; 
          margin: 0; 
        }
        :focus:not(:focus-visible) { outline: none; }
        :focus-visible { outline: 3px solid var(--color-leaf-400); outline-offset: 2px; }
        .skip-link { 
          position: absolute; top: -100%; left: 50%; transform: translateX(-50%); 
          z-index: 10000; padding: 12px 24px; background: var(--color-leaf-500); 
          color: var(--color-night-950); font-weight: 700; border-radius: 8px; 
          text-decoration: none; transition: top 0.2s ease; 
        }
        .skip-link:focus { top: 16px; }
        .sr-only { 
          position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; 
          overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; 
        }
        .sr-only:focus { 
          position: absolute; width: auto; height: auto; padding: 12px 24px; margin: 0; 
          overflow: visible; clip: auto; white-space: normal; 
          background: var(--color-leaf-500); color: var(--color-night-950); 
          font-weight: 700; border-radius: 8px; z-index: 10000; 
        }
        .glass { 
          background: rgba(255, 255, 255, 0.04); 
          border: 1px solid rgba(255, 255, 255, 0.09); 
          backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); 
        }
        .text-gradient-leaf { 
          background: linear-gradient(120deg, #7ee2a8 10%, #45bcd4 60%, #e6b96b 110%); 
          -webkit-background-clip: text; background-clip: text; color: transparent; 
        }
        .ring-glow { 
          box-shadow: 0 0 0 1px rgba(126, 226, 168, 0.25), 0 0 42px -6px rgba(47, 179, 107, 0.45); 
        }
        .gradient-blob-leaf { 
          background: radial-gradient(circle, var(--color-leaf-500) 0%, transparent 70%); 
        }
        @media (prefers-reduced-motion: reduce) {
          *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.01ms !important;
            scroll-behavior: auto !important;
          }
        }
        @media (prefers-contrast: high) {
          .glass { background: rgba(255, 255, 255, 0.1); border: 2px solid rgba(255, 255, 255, 0.3); }
          :focus-visible { outline-width: 4px; }
        }
      `.replace(/\s+/g, ' ').trim();
    },
    transformIndexHtml(html) {
      if (!isProduction || !criticalCSS) return html;
      
      // Inject critical CSS into the head
      const styleTag = `<style data-critical>${criticalCSS}</style>`;
      return html.replace('</head>', `${styleTag}\n</head>`);
    },
  };
}