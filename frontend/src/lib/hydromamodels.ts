/**
 * HyDroMa scientific models — TypeScript implementation of the formulas
 * published in the engineering booklets HP-01, HP-02 and HP-03 (v2).
 * Units follow the booklets: lengths in m, time in h/s, Q in m³/s.
 */

/** Horton infiltration rate, f(t) = fc + (f0−fc)·e^(−kt) [mm/h, t in h]. */
export function hortonRate(f0: number, fc: number, k: number, t: number): number {
  return fc + (f0 - fc) * Math.exp(-k * t);
}

/** Horton cumulative infiltration F(t) = fc·t + (f0−fc)/k·(1−e^(−kt)) [mm]. */
export function hortonCumulative(f0: number, fc: number, k: number, t: number): number {
  if (k <= 0) throw new Error('k must be positive');
  return fc * t + ((f0 - fc) / k) * (1 - Math.exp(-k * t));
}

/** SCS-CN potential retention S = 25400/CN − 254 [mm]. */
export function scsRetention(cn: number): number {
  if (cn <= 0 || cn > 100) throw new Error('CN must be in (0, 100]');
  return 25400 / cn - 254;
}

/** SCS-CN runoff Q = (P−0.2S)²/(P+0.8S) for P > 0.2S, else 0 [mm]. */
export function scsRunoff(rainfallP: number, cn: number): number {
  const s = scsRetention(cn);
  const initial = 0.2 * s;
  if (rainfallP <= initial) return 0;
  const numerator = (rainfallP - initial) ** 2;
  return numerator / (rainfallP - initial + s);
}

/** Van Genuchten water retention θ(h) with m = 1 − 1/n [cm³/cm³]. */
export function vanGenuchtenTheta(
  suctionHead: number,
  thetaR: number,
  thetaS: number,
  alpha: number,
  n: number,
): number {
  if (suctionHead < 0 || n <= 1) throw new Error('h ≥ 0 and n > 1 required');
  const m = 1 - 1 / n;
  const term = (1 + (alpha * suctionHead) ** n) ** m;
  return thetaR + (thetaS - thetaR) / term;
}

/** Darcy volumetric flow q = K·i·A [m³/s]; K [m/s], i [−], A [m²]. */
export function darcyFlow(conductivityK: number, gradientI: number, areaA: number): number {
  return conductivityK * gradientI * areaA;
}

/** Manning discharge Q = (1/n)·A·R^(2/3)·S^(1/2) [m³/s]. */
export function manningDischarge(n: number, areaA: number, radiusR: number, slopeS: number): number {
  if (n <= 0) throw new Error('n must be positive');
  return (1 / n) * areaA * radiusR ** (2 / 3) * Math.sqrt(slopeS);
}

/** Hydraulic radius R = A / P [m]. */
export function hydraulicRadius(areaA: number, wettedPerimeter: number): number {
  if (wettedPerimeter <= 0) throw new Error('P must be positive');
  return areaA / wettedPerimeter;
}

/** Reynolds number Re = ρ·v·D/μ (water default ρ=1000 kg/m³, μ=0.001 Pa·s). */
export function reynoldsNumber(velocity: number, depthD: number, rho = 1000, mu = 0.001): number {
  return (rho * velocity * depthD) / mu;
}

/** Froude number Fr = v/√(g·D) (g = 9.81 m/s²). */
export function froudeNumber(velocity: number, depthD: number, g = 9.81): number {
  return velocity / Math.sqrt(g * depthD);
}

/** Ring storage volume V = π·r²·h·n_eff [m³]. */
export function ringStorageVolume(radiusR: number, depthH: number, effectivePorosity: number): number {
  return Math.PI * radiusR * radiusR * depthH * effectivePorosity;
}

/** Effective porosity of layered fill n_eff = Σ(hi·ni)/Σhi [−]. */
export function effectivePorosity(layers: { thickness: number; porosity: number }[]): number {
  const total = layers.reduce((sum, layer) => sum + layer.thickness, 0);
  if (total <= 0) throw new Error('total thickness must be positive');
  return layers.reduce((sum, layer) => sum + layer.thickness * layer.porosity, 0) / total;
}

/** Francis weir discharge Q = 1.84·L·H^1.5 [m³/s], L and H in m. */
export function francisWeirDischarge(crestLengthL: number, headH: number): number {
  return 1.84 * crestLengthL * headH ** 1.5;
}

/** Horton decay coefficient from two rate observations. */
export function hortonK(f0: number, fc: number, t1: number, f1: number): number {
  const ratio = (f1 - fc) / (f0 - fc);
  if (ratio <= 0) throw new Error('f1 must be between fc and f0');
  return -Math.log(ratio) / t1;
}
