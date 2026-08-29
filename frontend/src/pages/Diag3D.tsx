/**
 * Simple diagnostic 3D scene - run at /diag3d
 * Tests if Three.js/OrbitControls work at all
 */
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';

function Box() {
  return (
    <mesh>
      <boxGeometry args={[2, 2, 2]} />
      <meshStandardMaterial color="orange" />
    </mesh>
  );
}

export default function Diag3D() {
  return (
    <div style={{
      width: '100vw', height: '100vh',
      background: '#0f172a', color: 'white',
      display: 'flex', flexDirection: 'column',
      fontFamily: 'Tahoma',
    }}>
      <div style={{ padding: '20px', background: '#1e293b' }}>
        <h1>🧪 3D Diagnostic Test</h1>
        <p>If the orange box appears and you can rotate it with mouse drag, 3D works!</p>
        <p>Controls: <b>Left+drag</b> = rotate, <b>scroll</b> = zoom, <b>right+drag</b> = pan</p>
      </div>
      <div style={{ flex: 1, position: 'relative' }}>
        <Canvas camera={{ position: [5, 5, 5], fov: 50 }}>
          <ambientLight intensity={0.5} />
          <directionalLight position={[5, 5, 5]} intensity={1} />
          <Box />
          <gridHelper args={[10, 10]} />
          <OrbitControls
            makeDefault
            enableDamping
            dampingFactor={0.1}
            enableRotate
            enableZoom
            enablePan
          />
        </Canvas>
      </div>
    </div>
  );
}
