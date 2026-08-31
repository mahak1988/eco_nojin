const section = {
  border: '1px solid var(--color-border)',
  borderRadius: 12,
  padding: '1rem 1.1rem',
  marginBottom: '0.8rem',
  background: 'var(--color-bg)',
};
const h2 = { fontSize: '0.95rem', fontWeight: 800, color: '#0d9488', margin: '0 0 0.5rem' };
const p = { fontSize: '0.82rem', color: 'var(--color-text)', lineHeight: 1.9, margin: '0.35rem 0' };
const wrap = { maxWidth: 900, margin: '0 auto', padding: '2rem 1rem' };
export default function Support() {
  const ways = [
    ['Financial Contributions', 'Sponsor specific features, models, or development sprints.'],
    ['Code Contributions', 'Bug fixes, new models, documentation on GitHub.'],
    ['Research Collaboration', 'Joint projects, validation studies, publications.'],
    ['Spread the Word', 'Cite HYDROMA, share on social media.'],
  ];
  return (
    <div style={wrap}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>
        Support Eco Nojin
      </h1>
      <div style={section}>
        {ways.map(([t, d]) => (
          <div
            key={t}
            style={{ borderBottom: '1px dashed var(--color-border)', padding: '0.5rem 0' }}
          >
            <div style={{ fontWeight: 800, fontSize: '0.85rem' }}>{t}</div>
            <p style={p}>{d}</p>
          </div>
        ))}
      </div>
      <div style={section}>
        <h2 style={h2}>Acknowledgments</h2>
        <p style={p}>
          USGS MODFLOW, FAO AquaCrop, CSDMS/Landlab, Natural Capital Project (InVEST), open-source
          GIS community.
        </p>
      </div>
    </div>
  );
}
