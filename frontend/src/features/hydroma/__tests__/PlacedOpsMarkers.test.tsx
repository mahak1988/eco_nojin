/**
 * PlacedOpsMarkers Tests
 * =======================
 * Unit tests for PlacedOpsMarkers component.
 */

import { describe, it, expect, vi } from 'vitest';
import { PlacedOpsMarkers } from '../components/canvas';
import type { PlacedOpsMarkersProps } from '../components/canvas/PlacedOpsMarkers';
import type { TerrainData, PlacedOp } from '../types';

describe('PlacedOpsMarkers Component', () => {
  describe('Exports', () => {
    it('should export PlacedOpsMarkers as a function', () => {
      expect(typeof PlacedOpsMarkers).toBe('function');
    });
  });

  describe('Props Interface', () => {
    it('should accept empty ops array', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10)
          .fill(0)
          .map(() => Array(10).fill(50)),
        moisture: Array(10)
          .fill(0)
          .map(() => Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      const onSelect = vi.fn();
      const props: PlacedOpsMarkersProps = {
        ops: [],
        data: terrain,
        selectedId: null,
        onSelect,
      };

      expect(props.ops).toEqual([]);
      expect(props.selectedId).toBeNull();
    });

    it('should accept multiple placed operations', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10)
          .fill(0)
          .map(() => Array(10).fill(50)),
        moisture: Array(10)
          .fill(0)
          .map(() => Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      const ops: PlacedOp[] = [
        { id: 'op-1', type: 'gabion', x: 5, y: 10, label: 'Gabion Wall' },
        { id: 'op-2', type: 'checkdam', x: -5, y: 3, label: 'Check Dam' },
        { id: 'op-3', type: 'terrace', x: 0, y: -8, label: 'Terrace' },
      ];

      const onSelect = vi.fn();
      const props: PlacedOpsMarkersProps = {
        ops,
        data: terrain,
        selectedId: 'op-1',
        onSelect,
      };

      expect(props.ops).toHaveLength(3);
      expect(props.selectedId).toBe('op-1');
    });

    it('should handle selected operation highlight', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10)
          .fill(0)
          .map(() => Array(10).fill(50)),
        moisture: Array(10)
          .fill(0)
          .map(() => Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      const op: PlacedOp = {
        id: 'op-1',
        type: 'gabion',
        x: 5,
        y: 10,
        label: 'Gabion',
      };

      const props: PlacedOpsMarkersProps = {
        ops: [op],
        data: terrain,
        selectedId: 'op-1',
        onSelect: vi.fn(),
      };

      expect(props.selectedId).toBe(op.id);
    });
  });
});
