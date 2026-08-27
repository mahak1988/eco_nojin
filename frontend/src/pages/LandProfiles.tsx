const section = { border: '1px solid var(--color-border)', borderRadius: 12, padding: '1rem 1.1rem', marginBottom: '0.8rem', background: 'var(--color-bg)' };
const h2 = { fontSize: '0.95rem', fontWeight: 800, color: '#0d9488', margin: '0 0 0.5rem' };
const p = { fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.9, margin: '0.35rem 0' };
const wrap = { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' };
const li = { fontSize: '0.8rem', color: 'var(--color-text)', lineHeight: 1.9 };
export default function LandProfiles() {
const dims = ['Physical (texture, structure, bulk density)', 'Chemical (pH, EC, OM, NPK)', 'Fertility (CEC, base saturation)', 'Water (field capacity, wilting point)'];
return (
  <div style={wrap}>
    <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>Land Profiles</h1>
    <div style={section}><h2 style={h2}>Profile dimensions</h2><ul style={{ paddingRight: '1.2rem', margin: 0 }}>{dims.map((x) => <li key={x} style={li}>{x}</li>)}</ul></div>
    <div style={section}><h2 style={h2}>Data sources</h2><p style={p}>SoilGrids (free) + lab samples + field pilots; every value is labelled with its source and confidence.</p></div>
  </div>
);
}
