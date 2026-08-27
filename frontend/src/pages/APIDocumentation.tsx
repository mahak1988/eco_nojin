const section = { border: '1px solid var(--color-border)', borderRadius: 12, padding: '1rem 1.1rem', marginBottom: '0.8rem', background: 'var(--color-bg)' };
const h2 = { fontSize: '0.95rem', fontWeight: 800, color: '#0d9488', margin: '0 0 0.5rem' };
const p = { fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.9, margin: '0.35rem 0' };
const wrap = { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' };
export default function APIDocumentation() {
const groups = [['Motors', '/api/v1/motors/drought · climate · calibrate'], ['Security', '/api/v1/security/status · anti-phishing'], ['OGC', '/ogc/features/v1 · /ogc/waterml/1.0'], ['Business', '/api/v1/materials · insurance · ecowallet · blockchain'], ['AI', '/api/v1/ai/advise']];
return (
  <div style={wrap}>
    <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>API Documentation</h1>
    <div style={section}>{groups.map(([n, e]) => <div key={n} style={{ borderBottom: '1px dashed var(--color-border)', padding: '0.45rem 0' }}><span style={{ fontWeight: 800, fontSize: '0.82rem' }}>{n}</span><div style={{ color: 'var(--color-text-secondary)', fontSize: '0.74rem', fontFamily: 'monospace' }}>{e}</div></div>)}</div>
    <div style={section}><h2 style={h2}>Interactive reference</h2><p style={p}>Full OpenAPI explorer: <a href="/docs" style={{ color: '#0d9488' }}>/docs</a> (Swagger UI) and <a href="/redoc" style={{ color: '#0d9488' }}>/redoc</a>.</p></div>
  </div>
);
}
