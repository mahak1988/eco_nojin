import { useEffect, useState } from 'react';
import './AdminTheme.css';

const API_BASE = 'http://localhost:8000/api/v1';

export default function AdminSecurity() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'ok' | 'failed'>('all');

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const url = API_BASE + '/admin/security';
        const res = await fetch(url, {
          headers: { Authorization: 'Bearer ' + token },
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const json = await res.json();
        setEvents(json.events || []);
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    fetchEvents();
  }, []);

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <div style={{ color: 'var(--text-muted)' }}>Loading security events...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
        <h3 style={{ color: 'var(--accent-danger)', margin: '0 0 8px 0' }}>Unable to load security events</h3>
        <p style={{ color: 'var(--text-muted)', margin: 0 }}>{error}</p>
      </div>
    );
  }

  const okEvents = events.filter(e => e.detail && e.detail.startsWith('ok'));
  const failedEvents = events.filter(e => e.detail && e.detail.startsWith('failed'));

  const filteredEvents = filter === 'all' ? events :
    filter === 'ok' ? okEvents : failedEvents;

  const successRate = events.length > 0 ? ((okEvents.length / events.length) * 100).toFixed(1) : '0';

  return (
    <div>
      {/* Security Summary */}
      <div className="info-banner">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: '0 0 8px 0', fontSize: '28px', fontWeight: 800 }}>
              Security Dashboard
            </h2>
            <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '14px' }}>
              Monitor authentication events and security incidents
            </p>
          </div>
          <div style={{
            padding: '12px 24px',
            background: 'rgba(16, 185, 129, 0.1)',
            borderRadius: '16px',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            textAlign: 'center',
          }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px', letterSpacing: '1px' }}>SUCCESS RATE</div>
            <div style={{ fontSize: '28px', fontWeight: 800, color: 'var(--accent-primary)' }}>{successRate}%</div>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="card-grid">
        <div className="stat-card">
          <div className="stat-label">Total Events</div>
          <div className="stat-value">{events.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Successful</div>
          <div className="stat-value" style={{ color: 'var(--accent-primary)' }}>{okEvents.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Failed Attempts</div>
          <div className="stat-value" style={{ color: 'var(--accent-danger)' }}>{failedEvents.length}</div>
        </div>
      </div>

      {/* Filters */}
      <div className="filter-bar">
        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginRight: '8px' }}>Filter:</div>
        {(['all', 'ok', 'failed'] as const).map((f) => (
          <button
            key={f}
            className={'filter-chip' + (filter === f ? ' active' : '')}
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'All' : f === 'ok' ? 'Success' : 'Failed'} ({f === 'all' ? events.length : f === 'ok' ? okEvents.length : failedEvents.length})
          </button>
        ))}
      </div>

      {/* Events Table */}
      <div className="glass-card">
        <div className="section-header" style={{ padding: '24px 24px 0 24px' }}>
          <div className="section-title">Authentication Events</div>
        </div>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Details</th>
              <th>IP Address</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '60px 20px' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.3 }}>🔒</div>
                  <div style={{ color: 'var(--text-muted)' }}>No authentication events found</div>
                </td>
              </tr>
            ) : (
              filteredEvents.map((event, i) => (
                <tr key={i}>
                  <td>
                    <span className={'status-badge ' + (event.detail && event.detail.startsWith('ok') ? 'success' : 'danger')}>
                      {event.detail && event.detail.startsWith('ok') ? '✓ Success' : '✗ Failed'}
                    </span>
                  </td>
                  <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                    {event.detail || '-'}
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '13px', color: 'var(--text-muted)' }}>
                    {event.ip_address || 'N/A'}
                  </td>
                  <td style={{ color: 'var(--text-faint)', fontSize: '13px' }}>
                    {event.created_at ? new Date(event.created_at).toLocaleString() : '-'}
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