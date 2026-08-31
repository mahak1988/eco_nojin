/**
 * HydromaViewport
 * =================
 * Main viewport wrapper that composes info bar + scene content.
 *
 * @module features/hydroma/components/viewport/HydromaViewport
 */

import { useHydromaStore } from '../../store';
import { TerrainMeshErrorBoundary } from '../canvas';
import { ViewportInfoBar } from './ViewportInfoBar';
import { SceneContent } from './SceneContent';
import { LoadingView } from './LoadingView';
import { EmptyView } from './EmptyView';

export function HydromaViewport() {
  const terrain = useHydromaStore((s) => s.terrain);
  const demLoading = useHydromaStore((s) => s.demLoading);

  return (
    <div
      style={{
        position: 'relative',
        background: '#0f172a',
        borderRadius: '16px',
        overflow: 'hidden',
        border: '1px solid rgba(255,255,255,0.1)',
        minHeight: '600px',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <ViewportInfoBar />

      <div style={{ flex: 1, position: 'relative', minHeight: '500px' }}>
        <TerrainMeshErrorBoundary>
          {terrain ? <SceneContent /> : demLoading ? <LoadingView /> : <EmptyView />}
        </TerrainMeshErrorBoundary>
      </div>
    </div>
  );
}
