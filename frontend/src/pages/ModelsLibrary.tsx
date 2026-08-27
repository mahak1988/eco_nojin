const section = { border: '1px solid var(--color-border)', borderRadius: 12, padding: '1rem 1.1rem', marginBottom: '0.8rem', background: 'var(--color-bg)' };
const h2 = { fontSize: '0.95rem', fontWeight: 800, color: '#0d9488', margin: '0 0 0.5rem' };
const p = { fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.9, margin: '0.35rem 0' };
const wrap = { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' };
export default function ModelsLibrary() {
const models = [['AquaCrop', 'FAO crop-water productivity'], ['RothC-26.3', 'Soil organic carbon turnover'], ['RUSLE', 'Water erosion'], ['SWAT+', 'Basin hydrology'], ['HEC-RAS', 'Flood hydraulics'], ['Pywr', 'Water resource allocation'], ['FAO-56', 'Evapotranspiration'], ['CMIP6 SSP', 'Climate scenarios']];
return (
  <div style={wrap}>
    <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>Models Library</h1>
    <div style={section}>{models.map(([n, d]) => <div key={n} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed var(--color-border)', padding: '0.45rem 0' }}><span style={{ fontWeight: 800, fontSize: '0.82rem' }}>{n}</span><span style={{ color: 'var(--color-text-secondary)', fontSize: '0.78rem' }}>{d}</span></div>)}</div>
    <div style={section}><h2 style={h2}>Open and free</h2><p style={p}>All scientific models run on free tiers (Open-Meteo, SoilGrids, Supabase) — no registration wall for the user.</p></div>
  </div>
);
}
