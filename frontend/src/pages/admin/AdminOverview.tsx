import { useEffect, useState } from 'react';

const API_BASE = 'http://localhost:8000/api/v1';

interface OverviewData {
  uptime_seconds: number;
  counts: {
    users: number;
    farms: number;
    audit_entries: number;
    errors_total: number;
    errors_open: number;
    content_total: number;
    content_published: number;
  };
  recent_audit: any[];
  recent_errors: any[];
}

export default function AdminOverview() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(${API_BASE}/admin/overview, {
          headers: { Authorization: Bearer  },
        });
        if (!res.ok) throw new Error(HTTP );
        const json = await res.json();
        setData(json);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>Loading overview...</div>;
  }
  if (error) {
    return (
      <div style={{ padding: '40px', color: '#dc2626', background: '#fee2e2', borderRadius: '8px' }}>
        Error loading overview: {error}
      </div>
    );
  }
  if (!data) return null;

  const stats = [
    { label: 'Users', value: data.counts.users, icon: 'users', color: '#3b82f6' },
    { label: 'Farms', value: data.counts.farms, icon: 'farm', color: '#10b981' },
    { label: 'Audit Logs', value: data.counts.audit_entries, icon: 'list', color: '#8b5cf6' },
    { label: 'Errors (Open)', value: data.counts.errors_open, icon: 'alert', color: '#ef4444' },
    { label: 'Content', value: data.counts.content_total, icon: 'file', color: '#f59e0b' },
    { label: 'Uptime', value: ${(data.uptime_seconds / 3600).toFixed(1)}h, icon: 'clock', color: '#6b7280' },
  ];

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        {stats.map((stat) => (
          <div key={stat.label} style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>{stat.label}</p>
                <p style={{ fontSize: '32px', fontWeight: 700, margin: '8px 0 0 0', color: stat.color }}>
                  {stat.value}
                </p>
              </div>
              <div style={{ fontSize: '40px', opacity: 0.2 }}>{stat.icon === 'users' ? 'U' : stat.icon === 'farm' ? 'F' : stat.icon === 'list' ? 'L' : stat.icon === 'alert' ? 'A' : stat.icon === 'file' ? 'D' : 'T'}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ background: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: '24px' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e5e7eb' }}>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>Recent Audit Logs</h3>
        </div>
        <div>
          {data.recent_audit.length === 0 ? (
            <p style={{ padding: '24px', color: '#6b7280', margin: 0 }}>No recent audit logs</p>
          ) : (
            data.recent_audit.slice(0, 10).map((log: any, i: number) => (
              <div key={i} style={{ padding: '16px 24px', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <p style={{ fontWeight: 500, margin: 0 }}>{log.action}</p>
                  <p style={{ fontSize: '13px', color: '#6b7280', margin: '4px 0 0 0' }}>{log.detail || JSON.stringify(log.details)}</p>
                </div>
                <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                  {log.created_at ? new Date(log.created_at).toLocaleString() : ''}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {data.recent_errors.length > 0 && (
        <div style={{ background: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div style={{ padding: '20px 24px', borderBottom: '1px solid #e5e7eb' }}>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>Recent Errors</h3>
          </div>
          <div>
            {data.recent_errors.map((err: any) => (
              <div key={err.id} style={{ padding: '16px 24px', borderBottom: '1px solid #f3f4f6' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <p style={{ fontWeight: 500, margin: 0 }}>{err.method} {err.path}</p>
                    <p style={{ fontSize: '13px', color: '#6b7280', margin: '4px 0 0 0' }}>{err.message}</p>
                  </div>
                  <span style={{
                    padding: '4px 8px',
                    fontSize: '12px',
                    borderRadius: '4px',
                    background: err.acked ? '#f3f4f6' : '#fee2e2',
                    color: err.acked ? '#6b7280' : '#dc2626',
                    fontWeight: 500,
                  }}>
                    {err.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
