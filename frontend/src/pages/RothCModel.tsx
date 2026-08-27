const section = { border: '1px solid var(--color-border)', borderRadius: 12, padding: '1rem 1.1rem', marginBottom: '0.8rem', background: 'var(--color-bg)' };
const h2 = { fontSize: '0.95rem', fontWeight: 800, color: '#0d9488', margin: '0 0 0.5rem' };
const p = { fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.9, margin: '0.35rem 0' };
const wrap = { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' };
const li = { fontSize: '0.8rem', color: 'var(--color-text)', lineHeight: 1.9 };
export default function RothCModel() {
const pools = ['Decomposable Plant Material (DPM)', 'Resistant Plant Material (RPM)', 'Microbial Biomass (BIO)', 'Humified Organic Matter (HUM)', 'Inert Organic Matter (IOM)'];
const drivers = ['Temperature', 'Moisture (open/closed)', 'Soil cover (bare/vegetated)', 'Clay content'];
return (
  <div style={wrap}>
    <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>RothC — Soil Carbon Turnover Model</h1>
    <div style={section}><h2 style={h2}>What it simulates</h2><p style={p}>RothC simulates the turnover of organic carbon in topsoil over decades, driven by climate, soil type and management. Eco Nojin runs it with real ERA5 climate and SoilGrids texture inputs.</p></div>
    <div style={section}><h2 style={h2}>Carbon pools</h2><ul style={{ paddingRight: '1.2rem', margin: 0 }}>{pools.map((x) => <li key={x} style={li}>{x}</li>)}</ul></div>
    <div style={section}><h2 style={h2}>Drivers</h2><ul style={{ paddingRight: '1.2rem', margin: 0 }}>{drivers.map((x) => <li key={x} style={li}>{x}</li>)}</ul></div>
    <div style={section}><h2 style={h2}>In the platform</h2><p style={p}>Run a scenario from the dashboard (RUSLE + RothC-lite in the browser for instant what-if, exact RothC-26.3 on the backend), then track SOC change year by year and feed the carbon-credit MRV chain.</p></div>
  </div>
);
}
