const section = { border: '1px solid var(--color-border)', borderRadius: 12, padding: '1rem 1.1rem', marginBottom: '0.8rem', background: 'var(--color-bg)' };
const h2 = { fontSize: '0.95rem', fontWeight: 800, color: '#0d9488', margin: '0 0 0.5rem' };
const p = { fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.9, margin: '0.35rem 0' };
const wrap = { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' };
export default function HelpDocs() {
const docs = [['Setup &amp; login', '/docs/fa/47_phase6_user_actions.md'], ['Phase 8-B simulators', '/docs/fa/55_phase8b_simulators.md'], ['Security &amp; OGC', '/docs/fa/56_phase8c_security_ogc_ai.md'], ['Deploy + domain + LLM', '/docs/fa/57_deploy_domain_llm.md']];
return (
  <div style={wrap}>
    <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>Help &amp; Documentation</h1>
    <div style={section}>{docs.map(([n, h]) => <div key={n} style={{ borderBottom: '1px dashed var(--color-border)', padding: '0.5rem 0' }}><a href={h} style={{ color: '#0d9488', fontWeight: 700, fontSize: '0.85rem' }}>{n}</a></div>)}</div>
    <div style={section}><h2 style={h2}>Quick answers</h2><p style={p}>Use the AI advice card on the dashboard for natural-language recommendations backed by the knowledge base.</p></div>
  </div>
);
}
