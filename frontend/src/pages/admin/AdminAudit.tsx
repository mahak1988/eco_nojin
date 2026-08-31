import { useEffect, useState } from 'react';
import './AdminTheme.css';

const API_BASE = 'http://localhost:8000/api/v1';

interface AuditEntry {
  id: string;
  actor_email: string;
  action: string;
  target: string;
  detail: string;
  created_at: string;
}

export default function AdminAudit() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAuditLogs = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(API_BASE + '/admin/audit', {
          headers: { Authorization: 'Bearer ' + token },
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const json = await res.json();
        setEntries(Array.isArray(json) ? json : json.entries || []);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchAuditLogs();
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <div style={{ color: 'var(--text-muted)' }}>Loading audit logs...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
        <h3 style={{ color: 'var(--accent-danger)', margin: '0 0 8px 0' }}>
          Unable to load audit logs
        </h3>
        <p style={{ color: 'var(--text-muted)', margin: 0 }}>{error}</p>
      </div>
    );
  }

  return (
    <div>
      <div className="info-banner">
        <h2 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: 700 }}>Audit Logs</h2>
        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '14px' }}>
          Complete history of all system actions ({entries.length} events)
        </p>
      </div>

      <div className="glass-card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Action</th>
              <th>Actor</th>
              <th>Target</th>
              <th>Detail</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {entries.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '60px 20px' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.3 }}>📋</div>
                  <div style={{ color: 'var(--text-muted)' }}>No audit logs found</div>
                </td>
              </tr>
            ) : (
              entries.map((entry) => (
                <tr key={entry.id}>
                  <td>
                    <span className="status-badge info">{entry.action}</span>
                  </td>
                  <td style={{ color: 'var(--text-primary)', fontWeight: 500 }}>
                    {entry.actor_email || '-'}
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{entry.target || '-'}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '13px', maxWidth: '300px' }}>
                    <div
                      style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                    >
                      {entry.detail || '-'}
                    </div>
                  </td>
                  <td
                    style={{ color: 'var(--text-faint)', fontSize: '13px', whiteSpace: 'nowrap' }}
                  >
                    {entry.created_at ? new Date(entry.created_at).toLocaleString() : '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
