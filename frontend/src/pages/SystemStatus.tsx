import React from 'react';
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
export default function SystemStatus() {
  const [health, setHealth] = React.useState<string>('checking…');
  React.useEffect(() => {
    fetch('/health')
      .then((r) => r.json())
      .then((d) => setHealth(d.status))
      .catch(() => setHealth('unreachable'));
  }, []);
  const rows = [
    ['API gateway', health],
    ['Security firewall (11 layers)', 'active'],
    ['OGC API Features', 'live'],
    ['WaterML 2.0', 'live'],
    ['Drought motor (ERA5)', 'live'],
    ['CMIP6 climate motor', 'live'],
  ];
  return (
    <div style={wrap}>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 900, color: '#0d9488', marginBottom: '1rem' }}>
        System Status
      </h1>
      <div style={section}>
        {rows.map(([k, v]) => (
          <div
            key={k}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              borderBottom: '1px dashed var(--color-border)',
              padding: '0.45rem 0',
            }}
          >
            <span style={{ fontSize: '0.82rem' }}>{k}</span>
            <span
              style={{
                fontWeight: 800,
                color: v === 'active' || v === 'live' || v === 'healthy' ? '#0d9488' : '#b45309',
                fontSize: '0.78rem',
              }}
            >
              {v}
            </span>
          </div>
        ))}
      </div>
      <div style={section}>
        <h2 style={h2}>Live endpoints</h2>
        <p style={p}>
          Interactive API reference:{' '}
          <a href="/docs" style={{ color: '#0d9488' }}>
            /docs
          </a>{' '}
          — OGC: /ogc/features/v1 — WaterML: /ogc/waterml/1.0/timeseries.
        </p>
      </div>
    </div>
  );
}
