
import { describe, it, expect, beforeEach } from 'vitest';
import { useHydromaStore } from '../store/hydromaStore';

describe('hydromaStore - Enhanced Tests', () => {
  beforeEach(() => {
    // Reset store before each test
    useHydromaStore.setState({
      terrain: null,
      viewMode: '3d',
      layers: {
        soil: false,
        bedrock: false,
        moisture: false,
        roots: false,
        groundwater: false,
      },
      showNdvi: false,
      visual: {
        showDecor: true,
        cropVisual: 'corn',
        growth: 0.5,
      },
      plots: [],
      climate: {
        windDirection: 0,
        windSpeed: 0,
        rainOn: false,
      },
      placedOps: [],
      selectedOp: null,
      polygons: [],
      currentDrawing: null,
      tourOn: false,
      siteMeta: null,
    });
  });

  describe('View Mode Actions', () => {
    it('should set view mode to 2d', () => {
      const { setViewMode } = useHydromaStore.getState();
      setViewMode('2d');
      expect(useHydromaStore.getState().viewMode).toBe('2d');
    });

    it('should set view mode to 3d', () => {
      const { setViewMode } = useHydromaStore.getState();
      setViewMode('3d');
      expect(useHydromaStore.getState().viewMode).toBe('3d');
    });

    it('should toggle between view modes', () => {
      const { setViewMode } = useHydromaStore.getState();
      
      setViewMode('2d');
      expect(useHydromaStore.getState().viewMode).toBe('2d');
      
      setViewMode('3d');
      expect(useHydromaStore.getState().viewMode).toBe('3d');
    });
  });

  describe('Layer Actions', () => {
    it('should toggle soil layer', () => {
      const { toggleLayer } = useHydromaStore.getState();
      
      expect(useHydromaStore.getState().layers.soil).toBe(false);
      
      toggleLayer('soil');
      expect(useHydromaStore.getState().layers.soil).toBe(true);
      
      toggleLayer('soil');
      expect(useHydromaStore.getState().layers.soil).toBe(false);
    });

    it('should toggle multiple layers independently', () => {
      const { toggleLayer } = useHydromaStore.getState();
      
      toggleLayer('soil');
      toggleLayer('bedrock');
      toggleLayer('moisture');
      
      const { layers } = useHydromaStore.getState();
      expect(layers.soil).toBe(true);
      expect(layers.bedrock).toBe(true);
      expect(layers.moisture).toBe(true);
      expect(layers.roots).toBe(false);
      expect(layers.groundwater).toBe(false);
    });

    it('should toggle NDVI separately', () => {
      const { toggleNdvi } = useHydromaStore.getState();
      
      expect(useHydromaStore.getState().showNdvi).toBe(false);
      
      toggleNdvi();
      expect(useHydromaStore.getState().showNdvi).toBe(true);
      
      toggleNdvi();
      expect(useHydromaStore.getState().showNdvi).toBe(false);
    });
  });

  describe('Visual Actions', () => {
    it('should toggle decor visibility', () => {
      const { toggleDecor } = useHydromaStore.getState();
      
      expect(useHydromaStore.getState().visual.showDecor).toBe(true);
      
      toggleDecor();
      expect(useHydromaStore.getState().visual.showDecor).toBe(false);
    });

    it('should set crop visual type', () => {
      const { setCropVisual } = useHydromaStore.getState();
      
      setCropVisual('wheat');
      expect(useHydromaStore.getState().visual.cropVisual).toBe('wheat');
      
      setCropVisual('corn');
      expect(useHydromaStore.getState().visual.cropVisual).toBe('corn');
    });

    it('should set growth level', () => {
      const { setGrowth } = useHydromaStore.getState();
      
      setGrowth(0.75);
      expect(useHydromaStore.getState().visual.growth).toBe(0.75);
      
      setGrowth(1.0);
      expect(useHydromaStore.getState().visual.growth).toBe(1.0);
    });
  });

  describe('Plot Actions', () => {
    it('should add a plot', () => {
      const { addPlot } = useHydromaStore.getState();
      
      addPlot({
        id: 'plot-1',
        center: [10, 20],
        size: [5, 5],
        data: { moisture: 0.5, ndvi: 0.8 },
      });
      
      const { plots } = useHydromaStore.getState();
      expect(plots).toHaveLength(1);
      expect(plots[0].id).toBe('plot-1');
    });

    it('should add multiple plots', () => {
      const { addPlot } = useHydromaStore.getState();
      
      addPlot({ id: 'plot-1', center: [0, 0], size: [1, 1], data: {} });
      addPlot({ id: 'plot-2', center: [10, 10], size: [2, 2], data: {} });
      addPlot({ id: 'plot-3', center: [20, 20], size: [3, 3], data: {} });
      
      expect(useHydromaStore.getState().plots).toHaveLength(3);
    });

    it('should remove a plot by id', () => {
      const { addPlot, removePlot } = useHydromaStore.getState();
      
      addPlot({ id: 'plot-1', center: [0, 0], size: [1, 1], data: {} });
      addPlot({ id: 'plot-2', center: [10, 10], size: [2, 2], data: {} });
      
      removePlot('plot-1');
      
      const { plots } = useHydromaStore.getState();
      expect(plots).toHaveLength(1);
      expect(plots[0].id).toBe('plot-2');
    });

    it('should handle removing non-existent plot', () => {
      const { removePlot } = useHydromaStore.getState();
      
      removePlot('non-existent');
      
      expect(useHydromaStore.getState().plots).toHaveLength(0);
    });
  });

  describe('Climate Actions', () => {
    it('should set wind direction', () => {
      const { setWindDirection } = useHydromaStore.getState();
      
      setWindDirection(180);
      expect(useHydromaStore.getState().climate.windDirection).toBe(180);
    });

    it('should set wind speed', () => {
      const { setWindSpeed } = useHydromaStore.getState();
      
      setWindSpeed(5.5);
      expect(useHydromaStore.getState().climate.windSpeed).toBe(5.5);
    });

    it('should toggle rain', () => {
      const { toggleRain } = useHydromaStore.getState();
      
      expect(useHydromaStore.getState().climate.rainOn).toBe(false);
      
      toggleRain();
      expect(useHydromaStore.getState().climate.rainOn).toBe(true);
      
      toggleRain();
      expect(useHydromaStore.getState().climate.rainOn).toBe(false);
    });
  });

  describe('Operation Actions', () => {
    it('should add placed operation', () => {
      const { addPlacedOp } = useHydromaStore.getState();
      
      addPlacedOp({
        id: 'op-1',
        type: 'irrigation',
        position: [10, 0, 20],
        timestamp: Date.now(),
      });
      
      const { placedOps } = useHydromaStore.getState();
      expect(placedOps).toHaveLength(1);
      expect(placedOps[0].id).toBe('op-1');
    });

    it('should select operation', () => {
      const { setSelectedOp } = useHydromaStore.getState();
      
      setSelectedOp('op-1');
      expect(useHydromaStore.getState().selectedOp).toBe('op-1');
      
      setSelectedOp(null);
      expect(useHydromaStore.getState().selectedOp).toBe(null);
    });

    it('should remove placed operation', () => {
      const { addPlacedOp, removePlacedOp } = useHydromaStore.getState();
      
      addPlacedOp({
        id: 'op-1',
        type: 'irrigation',
        position: [10, 0, 20],
        timestamp: Date.now(),
      });
      
      removePlacedOp('op-1');
      
      expect(useHydromaStore.getState().placedOps).toHaveLength(0);
    });
  });

  describe('Polygon Actions', () => {
    it('should add polygon', () => {
      const { addPolygon } = useHydromaStore.getState();
      
      addPolygon({
        id: 'poly-1',
        points: [[0, 0], [10, 0], [10, 10], [0, 10]],
        type: 'field',
      });
      
      const { polygons } = useHydromaStore.getState();
      expect(polygons).toHaveLength(1);
      expect(polygons[0].id).toBe('poly-1');
    });

    it('should remove polygon', () => {
      const { addPolygon, removePolygon } = useHydromaStore.getState();
      
      addPolygon({
        id: 'poly-1',
        points: [[0, 0], [10, 0], [10, 10], [0, 10]],
        type: 'field',
      });
      
      removePolygon('poly-1');
      
      expect(useHydromaStore.getState().polygons).toHaveLength(0);
    });

    it('should set current drawing', () => {
      const { setCurrentDrawing } = useHydromaStore.getState();
      
      setCurrentDrawing({
        points: [[0, 0], [5, 5]],
        type: 'field',
      });
      
      expect(useHydromaStore.getState().currentDrawing).toBeDefined();
      expect(useHydromaStore.getState().currentDrawing!.points).toHaveLength(2);
    });

    it('should clear current drawing', () => {
      const { setCurrentDrawing, clearCurrentDrawing } = useHydromaStore.getState();
      
      setCurrentDrawing({
        points: [[0, 0], [5, 5]],
        type: 'field',
      });
      
      clearCurrentDrawing();
      
      expect(useHydromaStore.getState().currentDrawing).toBe(null);
    });
  });

  describe('Tour Actions', () => {
    it('should toggle tour', () => {
      const { toggleTour } = useHydromaStore.getState();
      
      expect(useHydromaStore.getState().tourOn).toBe(false);
      
      toggleTour();
      expect(useHydromaStore.getState().tourOn).toBe(true);
      
      toggleTour();
      expect(useHydromaStore.getState().tourOn).toBe(false);
    });
  });

  describe('Terrain Actions', () => {
    it('should set terrain', () => {
      const { setTerrain } = useHydromaStore.getState();
      
      const mockTerrain = {
        width: 100,
        height: 100,
        elevation: [[0]],
      };
      
      setTerrain(mockTerrain as any);
      
      expect(useHydromaStore.getState().terrain).toBeDefined();
      expect(useHydromaStore.getState().terrain!.width).toBe(100);
    });

    it('should update terrain with function', () => {
      const { setTerrain } = useHydromaStore.getState();
      
      const initialTerrain = {
        width: 100,
        height: 100,
        elevation: [[0]],
      };
      
      setTerrain(initialTerrain as any);
      
      setTerrain((prev) => ({
        ...prev!,
        width: 200,
      }));
      
      expect(useHydromaStore.getState().terrain!.width).toBe(200);
    });
  });

  describe('Site Meta Actions', () => {
    it('should set site meta', () => {
      const { setSiteMeta } = useHydromaStore.getState();
      
      setSiteMeta({
        name: 'Test Site',
        lat: 40.0,
        lon: 50.0,
        elevation: 1000,
      });
      
      expect(useHydromaStore.getState().siteMeta).toBeDefined();
      expect(useHydromaStore.getState().siteMeta!.name).toBe('Test Site');
    });
  });
});
