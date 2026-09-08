import { describe, expect, it } from 'vitest';
import {
  darcyFlow,
  effectivePorosity,
  francisWeirDischarge,
  froudeNumber,
  hortonCumulative,
  hortonRate,
  hydraulicRadius,
  manningDischarge,
  reynoldsNumber,
  ringStorageVolume,
  scsRetention,
  scsRunoff,
  vanGenuchtenTheta,
} from '../lib/hydromamodels';

describe('Horton infiltration (HP-01 / HP-03, F-01)', () => {
  it('approaches the final rate over time', () => {
    // HP-01: fc=40, f0=130, k≈0.5/h
    expect(hortonRate(130, 40, 0.5, 0)).toBeCloseTo(130, 6);
    expect(hortonRate(130, 40, 0.5, 6)).toBeCloseTo(44.48, 1);
    expect(hortonRate(130, 40, 0.5, 24)).toBeCloseTo(40, 0);
  });

  it('cumulative infiltration grows monotonically', () => {
    const f0 = 130;
    const fc = 40;
    const k = 0.5;
    const at1 = hortonCumulative(f0, fc, k, 1);
    const at3 = hortonCumulative(f0, fc, k, 3);
    expect(at3).toBeGreaterThan(at1);
    expect(at1).toBeGreaterThan(0);
  });
});

describe('SCS-CN runoff (HP-01/03, F-02/03)', () => {
  it('computes retention from CN', () => {
    expect(scsRetention(80)).toBeCloseTo(25400 / 80 - 254, 6);
  });

  it('produces the known example for CN=80, P=50 mm', () => {
    const s = scsRetention(80); // 63.5 mm
    const q = scsRunoff(50, 80);
    expect(s).toBeCloseTo(63.5, 1);
    expect(q).toBeCloseTo((50 - 0.2 * s) ** 2 / (50 + 0.8 * s), 5);
  });

  it('returns zero below the initial abstraction', () => {
    expect(scsRunoff(5, 90)).toBe(0);
  });

  it('reduces runoff when CN drops (HP-01 goal 85 → 40)', () => {
    const before = scsRunoff(40, 85);
    const after = scsRunoff(40, 40);
    expect(after).toBeLessThan(before * 0.5);
  });
});

describe('Van Genuchten retention (HP-01/06, F-04)', () => {
  it('stays between residual and saturated water content', () => {
    for (const h of [1, 10, 100, 1000, 10000]) {
      const theta = vanGenuchtenTheta(h, 0.05, 0.45, 0.02, 1.5);
      expect(theta).toBeGreaterThanOrEqual(0.05);
      expect(theta).toBeLessThanOrEqual(0.45);
    }
  });

  it('decreases monotonically with suction', () => {
    const low = vanGenuchtenTheta(5, 0.05, 0.45, 0.02, 1.5);
    const high = vanGenuchtenTheta(500, 0.05, 0.45, 0.02, 1.5);
    expect(high).toBeLessThan(low);
  });
});

describe('Darcy + Manning hydraulics (HP-01 F-06 / HP-02 F-02)', () => {
  it('darcy flow scales with gradient and area', () => {
    const q1 = darcyFlow(1e-4, 0.02, 10);
    const q2 = darcyFlow(1e-4, 0.04, 10);
    expect(q2).toBeCloseTo(2 * q1, 10);
  });

  it('manning discharge sanity (trapezoid-like values)', () => {
    const q = manningDischarge(0.03, 0.5, 0.25, 0.01);
    expect(q).toBeGreaterThan(0);
    expect(q).toBeLessThan(10);
  });

  it('hydraulic radius is area over wetted perimeter', () => {
    expect(hydraulicRadius(4, 8)).toBeCloseTo(0.5, 6);
  });
});

describe('Dimensionless numbers + ring storage (HP-02/03)', () => {
  it('reynolds and froude sanity', () => {
    expect(reynoldsNumber(0.5, 0.2)).toBeCloseTo(100000, 3);
    expect(froudeNumber(0.5, 0.2)).toBeLessThan(1); // sub-critical
  });

  it('ring storage volume (HP-03: 740 L target)', () => {
    const volumeM3 = ringStorageVolume(0.75, 0.9, 0.45);
    expect(volumeM3 * 1000).toBeGreaterThan(500); // litres, order-of-magnitude check
    expect(volumeM3 * 1000).toBeLessThan(1000);
  });

  it('effective porosity of layered fill', () => {
    const n = effectivePorosity([
      { thickness: 0.3, porosity: 0.4 },
      { thickness: 0.3, porosity: 0.6 },
    ]);
    expect(n).toBeCloseTo(0.5, 6);
  });

  it('francis weir discharge (HP-02 F-08)', () => {
    expect(francisWeirDischarge(2, 0.5)).toBeCloseTo(1.84 * 2 * Math.sqrt(0.125), 5);
  });
});
