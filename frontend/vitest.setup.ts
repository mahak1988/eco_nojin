import "@testing-library/jest-dom/vitest";

// jsdom lacks ResizeObserver (needed by cmdk/radix)
if (typeof globalThis.ResizeObserver === "undefined") {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  (globalThis as any).ResizeObserver = ResizeObserverStub;
}
// jsdom lacks scrollIntoView
if (typeof Element.prototype.scrollIntoView !== "function") {
  (Element.prototype as any).scrollIntoView = () => {};
}
