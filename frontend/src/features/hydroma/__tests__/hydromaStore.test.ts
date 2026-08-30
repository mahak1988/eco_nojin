/**
 * HyDroMa Store Tests
 * ====================
 * Comprehensive tests for Zustand store.
 *
 * Tests cover:
 * - Initial state
 * - All actions
 * - Selectors
 * - Reset functionality
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { useHydromaStore } from '../store';
import type { TerrainData, PlacedOp, Polygon, DataPlot } from '../types';

describe('HyDroMa Store', () => {
  beforeEach(() => {
    // Reset store before each test
    useHydromaStore.getState().reset();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useHydromaStore.getState();

      expect(state.terrain).toBeNull();
      expect(state.viewMode).toBe('3d');
      expect(state.toolMode).toBe('orbit');
      expect(state.selectedOpType).toBeNull();
      expect(state.placedOps).toEqual([]);
      expect(state.polygons).toEqual([]);
      expect(state.plots).toEqual([]);
      expect(state.demLoading).toBe(false);
      expect(state.demError).toBe('');
    });

    it('should have correct visual defaults', () => {
      const { visual } = useHydromaStore.getState();

      expect(visual.showDecor).toBe(true);
      expect(visual.growth).toBe(0.6);
      expect(visual.cropVisual).toBe('corn');
    });

    it('should have correct climate defaults', () => {
      const { climate } = useHydromaStore.getState();

      expect(climate.windSpeed).toBe(15);
      expect(climate.windDirection).toBe(180);
      expect(climate.rainOn).toBe(false);
    });

    it('should have all layers disabled by default', () => {
      const { layers } = useHydromaStore.getState();

      expect(layers.soil).toBe(false);
      expect(layers.bedrock).toBe(false);
      expect(layers.moisture).toBe(false);
      expect(layers.roots).toBe(false);
      expect(layers.groundwater).toBe(false);
      expect(layers.ndvi).toBe(false);
    });
  });

  describe('Core Actions', () => {
    it('should set terrain', () => {
      const terrain: TerrainData = {
        width: 10,
        height: 10,
        elevation: Array(10).fill(Array(10).fill(0)),
        moisture: Array(10).fill(Array(10).fill(0.5)),
        minElevation: 0,
        maxElevation: 100,
      };

      useHydromaStore.getState().setTerrain(terrain);
      expect(useHydromaStore.getState().terrain).toEqual(terrain);
    });

    it('should set view mode', () => {
      useHydromaStore.getState().setViewMode('2d-top');
      expect(useHydromaStore.getState().viewMode).toBe('2d-top');
    });

    it('should set tool mode', () => {
      useHydromaStore.getState().setToolMode('draw-polygon');
      expect(useHydromaStore.getState().toolMode).toBe('draw-polygon');
    });

    it('should set selected operation type', () => {
      useHydromaStore.getState().setSelectedOpType('gabion');
      expect(useHydromaStore.getState().selectedOpType).toBe('gabion');
    });
  });

  describe('Placed Operations', () => {
    it('should add placed operation', () => {
      const op: PlacedOp = {
        id: 'op-1',
        type: 'gabion',
        x: 5,
        y: 10,
        label: 'Gabion Wall',
      };

      useHydromaStore.getState().addPlacedOp(op);
      expect(useHydromaStore.getState().placedOps).toHaveLength(1);
      expect(useHydromaStore.getState().placedOps[0]).toEqual(op);
    });

    it('should remove placed operation', () => {
      const op: PlacedOp = {
        id: 'op-1',
        type: 'gabion',
        x: 5,
        y: 10,
        label: 'Gabion Wall',
      };

      useHydromaStore.getState().addPlacedOp(op);
      useHydromaStore.getState().removePlacedOp('op-1');
      expect(useHydromaStore.getState().placedOps).toHaveLength(0);
    });

    it('should clear all placed operations', () => {
      const ops: PlacedOp[] = [
        { id: 'op-1', type: 'gabion', x: 5, y: 10, label: 'Gabion 1' },
        { id: 'op-2', type: 'checkdam', x: 15, y: 20, label: 'Check Dam' },
      ];

      ops.forEach((op) => useHydromaStore.getState().addPlacedOp(op));
      expect(useHydromaStore.getState().placedOps).toHaveLength(2);

      useHydromaStore.getState().clearPlacedOps();
      expect(useHydromaStore.getState().placedOps).toHaveLength(0);
    });
  });

  describe('Polygons', () => {
    it('should add drawing point', () => {
      useHydromaStore.getState().addDrawingPoint({ x: 5, y: 10 });
      expect(useHydromaStore.getState().currentDrawing).toHaveLength(1);
    });

    it('should clear drawing', () => {
      useHydromaStore.getState().addDrawingPoint({ x: 5, y: 10 });
      useHydromaStore.getState().addDrawingPoint({ x: 15, y: 20 });
      useHydromaStore.getState().clearDrawing();
      expect(useHydromaStore.getState().currentDrawing).toHaveLength(0);
    });

    it('should add polygon and clear drawing', () => {
      useHydromaStore.getState().addDrawingPoint({ x: 0, y: 0 });
      useHydromaStore.getState().addDrawingPoint({ x: 10, y: 0 });
      useHydromaStore.getState().addDrawingPoint({ x: 10, y: 10 });

      const polygon: Polygon = {
        id: 'poly-1',
        points: [
          { x: 0, y: 0 },
          { x: 10, y: 0 },
          { x: 10, y: 10 },
        ],
        name: 'Area 1',
        color: '#10b981',
        area: 50,
      };

      useHydromaStore.getState().addPolygon(polygon);

      expect(useHydromaStore.getState().polygons).toHaveLength(1);
      expect(useHydromaStore.getState().currentDrawing).toHaveLength(0);
    });

    it('should remove polygon', () => {
      const polygon: Polygon = {
        id: 'poly-1',
        points: [
          { x: 0, y: 0 },
          { x: 10, y: 0 },
          { x: 10, y: 10 },
        ],
        name: 'Area 1',
        color: '#10b981',
      };

      useHydromaStore.getState().addPolygon(polygon);
      useHydromaStore.getState().removePolygon('poly-1');
      expect(useHydromaStore.getState().polygons).toHaveLength(0);
    });
  });

  describe('Plots', () => {
    it('should add plot', () => {
      const plot: DataPlot = {
        id: 'plot-1',
        center: [5, 10],
        size: [6, 5],
        data: {
          moisture: 0.6,
          ndvi: 0.8,
          elevation: 150,
        },
      };

      useHydromaStore.getState().addPlot(plot);
      expect(useHydromaStore.getState().plots).toHaveLength(1);
    });

    it('should clear plots', () => {
      const plots: DataPlot[] = [
        {
          id: 'plot-1',
          center: [5, 10],
          size: [6, 5],
          data: { moisture: 0.6, ndvi: 0.8, elevation: 150 },
        },
        {
          id: 'plot-2',
          center: [15, 20],
          size: [6, 5],
          data: { moisture: 0.4, ndvi: 0.5, elevation: 200 },
        },
      ];

      plots.forEach((plot) => useHydromaStore.getState().addPlot(plot));
      useHydromaStore.getState().clearPlots();
      expect(useHydromaStore.getState().plots).toHaveLength(0);
    });
  });

  describe('Layers', () => {
    it('should toggle layer', () => {
      useHydromaStore.getState().toggleLayer('soil');
      expect(useHydromaStore.getState().layers.soil).toBe(true);

      useHydromaStore.getState().toggleLayer('soil');
      expect(useHydromaStore.getState().layers.soil).toBe(false);
    });

    it('should set layer visibility', () => {
      useHydromaStore.getState().setLayerVisibility('moisture', true);
      expect(useHydromaStore.getState().layers.moisture).toBe(true);
    });

    it('should reset layers to default', () => {
      useHydromaStore.getState().toggleLayer('soil');
      useHydromaStore.getState().toggleLayer('bedrock');
      useHydromaStore.getState().toggleLayer('moisture');

      useHydromaStore.getState().resetLayers();

      const { layers } = useHydromaStore.getState();
      expect(layers.soil).toBe(false);
      expect(layers.bedrock).toBe(false);
      expect(layers.moisture).toBe(false);
    });
  });

  describe('Climate', () => {
    it('should set wind speed', () => {
      useHydromaStore.getState().setWindSpeed(25);
      expect(useHydromaStore.getState().climate.windSpeed).toBe(25);
    });

    it('should set wind direction', () => {
      useHydromaStore.getState().setWindDirection(270);
      expect(useHydromaStore.getState().climate.windDirection).toBe(270);
    });

    it('should toggle rain', () => {
      expect(useHydromaStore.getState().climate.rainOn).toBe(false);

      useHydromaStore.getState().toggleRain();
      expect(useHydromaStore.getState().climate.rainOn).toBe(true);

      useHydromaStore.getState().toggleRain();
      expect(useHydromaStore.getState().climate.rainOn).toBe(false);
    });
  });

  describe('DEM State', () => {
    it('should set DEM loading', () => {
      useHydromaStore.getState().setDemLoading(true);
      expect(useHydromaStore.getState().demLoading).toBe(true);
    });

    it('should set DEM error', () => {
      useHydromaStore.getState().setDemError('Failed to load DEM');
      expect(useHydromaStore.getState().demError).toBe('Failed to load DEM');
    });

    it('should set site meta', () => {
      const meta = { lat: 35.7, lon: 51.4, siteId: 'SITE265' };
      useHydromaStore.getState().setSiteMeta(meta);
      expect(useHydromaStore.getState().siteMeta).toEqual(meta);
    });
  });

  describe('Reset', () => {
    it('should reset all state to initial', () => {
      // Modify state
      useHydromaStore.getState().setViewMode('2d-top');
      useHydromaStore.getState().setToolMode('draw-polygon');
      useHydromaStore.getState().addPlacedOp({
        id: 'op-1',
        type: 'gabion',
        x: 5,
        y: 10,
        label: 'Test',
      });
      useHydromaStore.getState().toggleLayer('soil');

      // Reset
      useHydromaStore.getState().reset();

      // Verify
      const state = useHydromaStore.getState();
      expect(state.viewMode).toBe('3d');
      expect(state.toolMode).toBe('orbit');
      expect(state.placedOps).toHaveLength(0);
      expect(state.layers.soil).toBe(false);
    });
  });
});
