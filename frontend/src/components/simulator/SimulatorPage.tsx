import { SimulatorCanvas } from './SimulatorCanvas';
import { SimulatorErrorBoundary } from './SimulatorErrorBoundary';
import { ControlPanel } from './ControlPanel';

/**
 * The public page component for /hydroma.
 * ErrorBoundary wraps the Canvas so crashes don't take down the app.
 */
export default function SimulatorPage() {
  return (
    <div style={{ width: '100%', height: '100vh', position: 'relative', background: '#0a0f1c' }}>
      <SimulatorErrorBoundary>
        <SimulatorCanvas />
      </SimulatorErrorBoundary>
      <ControlPanel />
      <div style={{
        position: 'absolute',
        bottom: 12,
        left: 12,
        color: 'rgba(255,255,255,0.45)',
        fontSize: 11,
        fontFamily: 'monospace',
        pointerEvents: 'none',
        zIndex: 100,
        direction: 'rtl',
      }}>
        شبیه‌ساز استاندارد v1 • Procedural • آفلاین کامل
      </div>
    </div>
  );
}
