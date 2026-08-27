const section = { border: '1px solid var(--color-border)', borderRadius: 12, padding: '1rem 1.1rem', marginBottom: '0.8rem', background: 'var(--color-bg)' };
const h2 = { fontSize: '0.95rem', fontWeight: 800, color: '#0d9488', margin: '0 0 0.5rem' };
const p = { fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.9, margin: '0.35rem 0' };
const wrap = { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' };
const li = { fontSize: '0.8rem', color: 'var(--color-text)', lineHeight: 1.9 };
export default function DataManagement() {
const flows = ['CSV import for Kobo field samples', 'Lab data upload (lab router)', 'Supabase cloud sync (RLS-protected)', 'OGC / WaterML exports'];
return (
  <div style={wrap}>
    <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>Data Management</h1>
    <div style={section}><h2 style={h2}>Data flows</h2><ul style={{ paddingRight: '1.2rem', margin: 0 }}>{flows.map((x) => <li key={x} style={li}>{x}</li>)}</ul></div>
    <div style={section}><h2 style={h2}>Privacy</h2><p style={p}>Row-level security on Supabase: farmers see only their own rows; admins get full access; everything is audited.</p></div>
  </div>
);
}
