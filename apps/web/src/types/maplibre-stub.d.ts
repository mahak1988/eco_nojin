// Type stub for maplibre-gl-js (scaffold — install with `pnpm add -D maplibre-gl-js` in Phase 3)
declare module 'maplibre-gl-js' {
  class Map {
    constructor(options: {
      container: HTMLElement | string;
      style?: string | object;
      center?: [number, number];
      zoom?: number;
    });
    on(event: string, handler: (...args: unknown[]) => void): void;
    queryRenderedFeatures(
      point?: { x: number; y: number },
      options?: { layers?: string[] },
    ): Array<{ properties?: Record<string, unknown> }>;
    addSource(id: string, source: Record<string, unknown>): void;
    addLayer(layer: Record<string, unknown>, before?: string): void;
    remove(): void;
  }

  export { Map };
  export function createMap(options: Record<string, unknown>): Map;
}

declare module 'maplibre-gl-js/css/maplibre-gl.css' {
  const css: string;
  export default css;
}
