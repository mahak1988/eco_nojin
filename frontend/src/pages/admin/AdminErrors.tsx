import { useEffect, useState } from 'react';
import './AdminTheme.css';

const API_BASE = 'http://localhost:8000/api/v1';

interface ErrorLog {
  id: string;
  method: string;
  path: string;
  status: number;
  message: string;
  acked: boolean;
  created_at: string;
}

export default function AdminErrors() {
  const [errors, setErrors] = useState<ErrorLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'open' | 'resolved'>('all');

  useEffect(() => {
    const fetchErrors = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(API_BASE + '/admin/errors', {
          headers: { Authorization: 'Bearer ' + token },
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const json = await res.json();
        setErrors(Array.isArray(json) ? json : json.errors || []);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchErrors();
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <div style={{ color: 'var(--text-muted)' }}>Loading errors...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
        <h3 style={{ color: 'var(--accent-danger)', margin: '0 0 8px 0' }}>Unable to load errors</h3>
        <p style={{ color: 'var(--text-muted)', margin: 0 }}>{error}</p>
      </div>
    );
  }

  const openErrors = errors.filter(e => !e.acked);
  const resolvedErrors = errors.filter(e => e.acked);
  const filteredErrors = filter === 'all' ? errors : filter === 'open' ? openErrors : resolvedErrors;

  return (
    <div>
      <div className="card-grid">
        <div className="stat-card">
          <div className="stat-label">Total Errors</div>
          <div className="stat-value">{errors.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Open Issues</div>
          <div className="stat-value" style={{ color: 'var(--accent-danger)' }}>{openErrors.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Resolved</div>
          <div className="stat-value" style={{ color: 'var(--accent-primary)' }}>{resolvedErrors.length}</div>
        </div>
      </div>

      <div className="filter-bar">
        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginRight: '8px' }}>Filter:</div>
        {(['all', 'open', 'resolved'] as const).map((f) => (
          <button key={f} className={'filter-chip' + (filter === f ? ' active' : '')} onClick={() => setFilter(f)}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="glass-card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Method</th>
              <th>Path</th>
              <th>Message</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {filteredErrors.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '60px 20px' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.3 }}>✅</div>
                  <div style={{ color: 'var(--text-muted)' }}>No errors found</div>
                </td>
              </tr>
            ) : (
              filteredErrors.map((err) => (
                <tr key={err.id}>
                  <td><span className={'status-badge ' + (err.acked ? 'success' : 'danger')}>{err.status}</span></td>
                  <td><span className="status-badge info">{err.method}</span></td>
                  <td style={{ fontFamily: 'monospace', fontSize: '12px', color: 'var(--accent-primary)' }}>{err.path}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '13px', maxWidth: '400px' }}>
                    <div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{err.message}</div>
                  </td>
                  <td style={{ color: 'var(--text-faint)', fontSize: '13px', whiteSpace: 'nowrap' }}>
                    {err.created_at ? new Date(err.created_at).toLocaleString() : '-'}
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
