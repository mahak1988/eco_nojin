import '@testing-library/jest-dom/vitest';

/**
 * jsdom lacks several browser APIs that framer-motion and testing-library
 * rely on. Provide minimal, inert stubs so components render in tests.
 */

class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}

class IntersectionObserverStub {
  readonly root: Element | null = null;
  readonly rootMargin: string = '';
  readonly thresholds: ReadonlyArray<number> = [];
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}

const win = window as unknown as Record<string, unknown>;

if (!('IntersectionObserver' in window)) {
  win.IntersectionObserver = IntersectionObserverStub;
}
if (!('ResizeObserver' in window)) {
  win.ResizeObserver = ResizeObserverStub;
}
if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: (): void => {},
      removeListener: (): void => {},
      addEventListener: (): void => {},
      removeEventListener: (): void => {},
      dispatchEvent: (): boolean => false,
    }),
  });
}

if (!('scrollTo' in window)) {
  win.scrollTo = (): void => {};
}
