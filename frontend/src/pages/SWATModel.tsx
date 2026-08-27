const section = { border: '1px solid var(--color-border)', borderRadius: 12, padding: '1rem 1.1rem', marginBottom: '0.8rem', background: 'var(--color-bg)' };
const h2 = { fontSize: '0.95rem', fontWeight: 800, color: '#0d9488', margin: '0 0 0.5rem' };
const p = { fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.9, margin: '0.35rem 0' };
const wrap = { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' };
const li = { fontSize: '0.8rem', color: 'var(--color-text)', lineHeight: 1.9 };
export default function SWATModel() {
const sims = ['Surface runoff', 'Sediment transport', 'Nutrient cycling (N, P)', 'Crop growth', 'Groundwater flow'];
return (
  <div style={wrap}>
    <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>SWAT — Soil &amp; Water Assessment Tool</h1>
    <div style={section}><h2 style={h2}>Basin-scale modelling</h2><p style={p}>SWAT is a river-basin scale model for long-term land-management impact assessment. Eco Nojin integrates its outputs for watershed planning and restoration prioritisation.</p></div>
    <div style={section}><h2 style={h2}>Simulates</h2><ul style={{ paddingRight: '1.2rem', margin: 0 }}>{sims.map((x) => <li key={x} style={li}>{x}</li>)}</ul></div>
    <div style={section}><h2 style={h2}>Honest status</h2><p style={p}>Full SWAT+ binary runs are heavy; the platform currently reports availability honestly per scenario and activates them when the runtime is provisioned.</p></div>
  </div>
);
}
