/**
 * HyDroMaCenter (Orchestrator)
 * ============================
 * Main entry point for Hydrological & Topographical Modeling Center.
 *
 * This file is now ONLY an orchestrator that composes:
 * - HydromaSidebar (left panel with all controls)
 * - HydromaViewport (right panel with 3D scene)
 *
 * All state is managed via Zustand store (hydromaStore).
 * All logic is in custom hooks (useRealDem, useTerrainClick, etc).
 * All rendering is in extracted components (canvas/, sidebar/, viewport/).
 *
 * Before: 8804 lines of monolithic code
 * After:  ~80 lines of clean orchestration
 *
 * @module pages/HyDroMaCenter
 */

import { useEffect } from 'react';
import { useRealDem } from '../features/hydroma/hooks';
import { HydromaSidebar } from '../features/hydroma/components/sidebar';
import { HydromaViewport } from '../features/hydroma/components/viewport';
import '../styles/hydroma.css';

export default function HyDroMaCenter() {
  // Initialize DEM loading on mount (uses Zustand store internally)
  const { loading, error } = useRealDem();

  // Global error logging
  useEffect(() => {
    if (error) {
      console.error('[HyDroMaCenter] DEM Error:', error);
    }
  }, [error]);

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '340px 1fr',
        gap: '16px',
        padding: '16px',
        height: 'calc(100vh - 60px)',
        minHeight: '600px',
        fontFamily: 'var(--font-persian, Tahoma, Arial, sans-serif)',
      }}
    >
      {/* LEFT SIDEBAR */}
      <HydromaSidebar />

      {/* RIGHT: 3D VIEWPORT */}
      <HydromaViewport />
    </div>
  );
}
