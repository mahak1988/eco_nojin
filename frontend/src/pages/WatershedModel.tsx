const section = { border: '1px solid var(--color-border)', borderRadius: 12, padding: '1rem 1.1rem', marginBottom: '0.8rem', background: 'var(--color-bg)' };
const h2 = { fontSize: '0.95rem', fontWeight: 800, color: '#0d9488', margin: '0 0 0.5rem' };
const p = { fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.9, margin: '0.35rem 0' };
const wrap = { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' };
const li = { fontSize: '0.8rem', color: 'var(--color-text)', lineHeight: 1.9 };
export default function WatershedModel() {
const steps = ['SCS-CN runoff estimation', 'Muskingum channel routing', 'FAO-56 evapotranspiration', 'Drought indices (SPI/SPEI)'];
return (
  <div style={wrap}>
    <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>Watershed Model — HyDroMa Engine</h1>
    <div style={section}><h2 style={h2}>Hydrological chain</h2><ul style={{ paddingRight: '1.2rem', margin: 0 }}>{steps.map((x) => <li key={x} style={li}>{x}</li>)}</ul></div>
    <div style={section}><h2 style={h2}>Free, real data</h2><p style={p}>Rainfall and temperature come from Open-Meteo ERA5 (no registration); soil data from SoilGrids. Band-sars (bendways) and French drains are evaluated as interventions.</p></div>
    <div style={section}><h2 style={h2}>Calibration</h2><p style={p}>CN, Ks, AWC and C/P factors are auto-calibrated against observed series (bounded search); without observations the API honestly returns requires_observed_data.</p></div>
  </div>
);
}
