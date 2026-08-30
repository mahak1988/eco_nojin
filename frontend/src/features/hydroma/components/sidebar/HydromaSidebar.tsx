/**
 * HydromaSidebar
 * ===============
 * Orchestrates all sidebar panels for HyDroMa Center.
 *
 * @module features/hydroma/components/sidebar/HydromaSidebar
 */

import TerrainBuilder from '../../../../components/simulators/TerrainBuilder';
import RealSiteLoader from '../../../../components/simulators/RealSiteLoader';
import { useHydromaStore } from '../../store';
import { DemStatus } from './DemStatus';
import { ErosionEffectPanel } from './ErosionEffectPanel';
import { ViewModeControls } from './ViewModeControls';
import { AtmosphereControls } from './AtmosphereControls';
import { ToolModeControls } from './ToolModeControls';
import { WindControls } from './WindControls';
import { VisualControls } from './VisualControls';
import { ScientificModelsSection } from './ScientificModelsSection';
import { LayersPanel } from './LayersPanel';
import { PlacedOpsList } from './PlacedOpsList';
import { PolygonsList } from './PolygonsList';
import { sidebarStyles } from './styles';

export function HydromaSidebar() {
  const setTerrain = useHydromaStore((s) => s.setTerrain);
  const setSiteMeta = useHydromaStore((s) => s.setSiteMeta);

  return (
    <div style={sidebarStyles.container}>
      {/* Generators */}
      <TerrainBuilder onGenerate={setTerrain} />
      <RealSiteLoader
        onLoaded={(t, meta) => {
          setTerrain(t);
          setSiteMeta(meta);
        }}
      />

      {/* Status */}
      <DemStatus />
      <ErosionEffectPanel />

      {/* View & Camera */}
      <ViewModeControls />
      <AtmosphereControls />

      {/* Tools */}
      <ToolModeControls />

      {/* Environment */}
      <WindControls />
      <VisualControls />

      {/* Science */}
      <ScientificModelsSection />

      {/* Layers */}
      <LayersPanel />

      {/* Lists */}
      <PlacedOpsList />
      <PolygonsList />
    </div>
  );
}
