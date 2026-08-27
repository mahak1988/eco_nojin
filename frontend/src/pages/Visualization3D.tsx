const section = { border: '1px solid var(--color-border)', borderRadius: 12, padding: '1rem 1.1rem', marginBottom: '0.8rem', background: 'var(--color-bg)' };
const h2 = { fontSize: '0.95rem', fontWeight: 800, color: '#0d9488', margin: '0 0 0.5rem' };
const p = { fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.9, margin: '0.35rem 0' };
const wrap = { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' };
export default function Visualization3D() {
return (
  <div style={wrap}>
    <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>3D Visualization</h1>
    <div style={section}><h2 style={h2}>Terrain &amp; land lab</h2><p style={p}>Interactive 3D terrain, water-infiltration and multi-layer farm scenes live in the Virtual Land Lab and Simulator Dashboard.</p></div>
    <div style={section}><h2 style={h2}>Go there</h2><p style={p}>Open <strong>Virtual Land Lab</strong> from the main navigation for the full 3D experience (WebGL, free).</p></div>
  </div>
);
}
