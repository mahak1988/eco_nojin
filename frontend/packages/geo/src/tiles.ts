/**
 * Tile providers we commonly use. Apps pass through `VITE_MAP_STYLE_URL`
 * to override at deploy time.
 */
export const TILE_PROVIDERS = {
  openfreemap: 'https://tiles.openfreemap.org/styles/liberty',
  openfreemapBright: 'https://tiles.openfreemap.org/styles/bright',
  opentopomap: 'https://a.tile.opentopomap.org/{z}/{x}/{y}.png',
  cartoVoyager: 'https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json',
} as const;

export type TileProvider = keyof typeof TILE_PROVIDERS;

export function tileUrl(provider: TileProvider): string {
  return TILE_PROVIDERS[provider];
}