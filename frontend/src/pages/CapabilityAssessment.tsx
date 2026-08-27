const section = { border: '1px solid var(--color-border)', borderRadius: 12, padding: '1rem 1.1rem', marginBottom: '0.8rem', background: 'var(--color-bg)' };
const h2 = { fontSize: '0.95rem', fontWeight: 800, color: '#0d9488', margin: '0 0 0.5rem' };
const p = { fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.9, margin: '0.35rem 0' };
const wrap = { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' };
const li = { fontSize: '0.8rem', color: 'var(--color-text)', lineHeight: 1.9 };
export default function CapabilityAssessment() {
const caps = ['Land capability classification', 'Irrigation suitability screening', 'Erosion risk rating (RUSLE)', 'Drought exposure (SPI/SPEI)', 'Carbon sequestration potential (RothC)'];
return (
  <div style={wrap}>
    <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>Capability Assessment</h1>
    <div style={section}><h2 style={h2}>Assessments available</h2><ul style={{ paddingRight: '1.2rem', margin: 0 }}>{caps.map((x) => <li key={x} style={li}>{x}</li>)}</ul></div>
    <div style={section}><h2 style={h2}>Method</h2><p style={p}>Free real data (ERA5, SoilGrids, Sentinel indices) with honest labelling of every method and uncertainty.</p></div>
  </div>
);
}
