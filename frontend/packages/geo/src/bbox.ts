import type { GeoBounds, GeoPoint } from '@eco/api/schema/common';

export function bboxToCenter(bounds: GeoBounds): GeoPoint {
  return { lat: (bounds.south + bounds.north) / 2, lon: (bounds.west + bounds.east) / 2 };
}

export function bboxArea(bounds: GeoBounds): number {
  // Equirectangular approx — good enough for UI display.
  const R = 6371000;
  const latRad = ((bounds.north - bounds.south) * Math.PI) / 180;
  const lonRad = ((bounds.east - bounds.west) * Math.PI) / 180;
  const meanLat = ((bounds.north + bounds.south) / 2 * Math.PI) / 180;
  return R * R * latRad * lonRad * Math.cos(meanLat);
}

export function bboxToMaplibreBounds(bounds: GeoBounds): [[number, number], [number, number]] {
  return [
    [bounds.west, bounds.south],
    [bounds.east, bounds.north],
  ];
}

export function pointInBounds(point: GeoPoint, bounds: GeoBounds): boolean {
  return (
    point.lat >= bounds.south &&
    point.lat <= bounds.north &&
    point.lon >= bounds.west &&
    point.lon <= bounds.east
  );
}

export function expandBounds(bounds: GeoBounds, factor = 1.1): GeoBounds {
  const cx = (bounds.west + bounds.east) / 2;
  const cy = (bounds.south + bounds.north) / 2;
  const halfW = ((bounds.east - bounds.west) * factor) / 2;
  const halfH = ((bounds.north - bounds.south) * factor) / 2;
  return {
    west: cx - halfW,
    east: cx + halfW,
    south: cy - halfH,
    north: cy + halfH,
  };
}