// Single Source of Truth for terrain elevation.
// EVERY component (terrain, grass, animals, water, structures) MUST use this.

class PerlinNoise {
  private p: number[];
  constructor(seed = 42) {
    this.p = [];
    for (let i = 0; i < 256; i++) this.p[i] = i;
    let n = seed;
    for (let i = 255; i > 0; i--) {
      n = (n * 9301 + 49297) % 233280;
      const j = Math.floor((n / 233280) * (i + 1));
      [this.p[i], this.p[j]] = [this.p[j], this.p[i]];
    }
    for (let i = 0; i < 256; i++) this.p[256 + i] = this.p[i];
  }
  private fade(t: number) { return t * t * t * (t * (t * 6 - 15) + 10); }
  private lerp(t: number, a: number, b: number) { return a + t * (b - a); }
  private grad(h: number, x: number, y: number) {
    const g = h & 7;
    const u = g < 4 ? x : y;
    const v = g < 4 ? y : x;
    return ((g & 1) ? -u : u) + ((g & 2) ? -v : v);
  }
  noise2D(x: number, y: number): number {
    const X = Math.floor(x) & 255, Y = Math.floor(y) & 255;
    x -= Math.floor(x); y -= Math.floor(y);
    const u = this.fade(x), v = this.fade(y);
    const A = this.p[X] + Y, B = this.p[X + 1] + Y;
    return this.lerp(v,
      this.lerp(u, this.grad(this.p[A], x, y), this.grad(this.p[B], x - 1, y)),
      this.lerp(u, this.grad(this.p[A + 1], x, y - 1), this.grad(this.p[B + 1], x - 1, y - 1)));
  }
  fbm(x: number, y: number, oct = 4): number {
    let t = 0, f = 1, a = 1, m = 0;
    for (let i = 0; i < oct; i++) { t += this.noise2D(x * f, y * f) * a; m += a; a *= 0.5; f *= 2; }
    return t / m;
  }
  ridged(x: number, y: number, oct = 4): number {
    let t = 0, f = 1, a = 1, m = 0;
    for (let i = 0; i < oct; i++) {
      const n = 1 - Math.abs(this.noise2D(x * f, y * f));
      t += n * n * a; m += a; a *= 0.5; f *= 2;
    }
    return t / m;
  }
}

export const perlin = new PerlinNoise(42);
export const TERRAIN_SIZE = 800;
export const LAKE_LEVEL = -1.3;

function smoothstep(e0: number, e1: number, x: number): number {
  const t = Math.min(1, Math.max(0, (x - e0) / (e1 - e0)));
  return t * t * (3 - 2 * t);
}

/**
 * World-space terrain height.
 * Design: flat farm valley at center (±1.5m), mountains at horizon (up to 45m).
 */
export function getTerrainHeight(x: number, z: number): number {
  const nx = x / TERRAIN_SIZE;
  const nz = z / TERRAIN_SIZE;

  // Far zone: mountains + hills
  const mountains = perlin.ridged(nx * 3 + 10, nz * 3 + 10, 4) * 40;
  const hills = perlin.fbm(nx * 5, nz * 5, 4) * 15;
  const detail = perlin.fbm(nx * 20, nz * 20, 3) * 2;
  const mountainous = mountains + hills + detail;

  // Near zone: gentle farm valley
  const farm = perlin.fbm(nx * 8, nz * 8, 2) * 1.5 + perlin.fbm(nx * 30, nz * 30, 2) * 0.3;

  const dist = Math.sqrt(x * x + z * z);
  const t = smoothstep(70, 240, dist);
  let h = farm * (1 - t) + mountainous * t;

  // Lake basin carve near center
  const lakeMask = Math.max(0, perlin.noise2D(nx * 2 + 5, nz * 2 + 5));
  h -= Math.pow(1 - lakeMask, 3) * 2.5 * (1 - t);

  return h;
}
