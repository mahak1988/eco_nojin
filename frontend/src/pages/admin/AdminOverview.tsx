import { useEffect, useState } from 'react';
import './AdminTheme.css';

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
        const url = API_BASE + '/admin/overview';
        const res = await fetch(url, {
          headers: { Authorization: 'Bearer ' + token },
        });
        if (!res.ok) throw new Error('HTTP ' + res.status);
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
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Loading dashboard data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
        <h3 style={{ color: 'var(--accent-danger)', margin: '0 0 8px 0' }}>Unable to load dashboard</h3>
        <p style={{ color: 'var(--text-muted)', margin: 0 }}>{error}</p>
        <button className="btn-primary" onClick={() => window.location.reload()} style={{ marginTop: '24px' }}>
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const stats = [
    { label: 'Total Users', value: data.counts.users, icon: '👥', color: '#3b82f6', trend: '+12%' },
    { label: 'Active Farms', value: data.counts.farms, icon: '🌾', color: '#10b981', trend: '+8%' },
    { label: 'Audit Logs', value: data.counts.audit_entries, icon: '📋', color: '#8b5cf6', trend: '+23%' },
    { label: 'Open Errors', value: data.counts.errors_open, icon: '⚡', color: '#ef4444', trend: '-5%' },
    { label: 'Total Content', value: data.counts.content_total, icon: '📄', color: '#f59e0b', trend: '+15%' },
    { label: 'System Uptime', value: (data.uptime_seconds / 3600).toFixed(1) + 'h', icon: '⚙️', color: '#06b6d4', trend: '99.9%' },
  ];

  const quickActions = [
    { icon: '👥', label: 'Manage Users', path: '/admin/users' },
    { icon: '📊', label: 'View Reports', path: '/admin/audit' },
    { icon: '⚙️', label: 'System Settings', path: '/admin/settings' },
    { icon: '🔒', label: 'Security Audit', path: '/admin/security' },
  ];

  const getIconBg = (color: string): React.CSSProperties => ({
    width: '48px',
    height: '48px',
    borderRadius: '12px',
    background: color + '22',
    border: '1px solid ' + color + '44',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '24px',
  });

  return (
    <div>
      {/* Welcome Banner */}
      <div className="info-banner">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: '0 0 8px 0', fontSize: '28px', fontWeight: 800, letterSpacing: '-0.5px' }}>
              Platform Overview
            </h2>
            <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '14px' }}>
              Real-time insights into your Eco Nojin platform
            </p>
          </div>
          <div style={{
            padding: '8px 16px',
            background: 'rgba(16, 185, 129, 0.1)',
            borderRadius: '20px',
            border: '1px solid rgba(16, 185, 129, 0.3)',
            fontSize: '12px',
            color: 'var(--accent-primary)',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            <div className="pulse-dot" />
            Live
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="card-grid">
        {stats.map((stat) => (
          <div key={stat.label} className="stat-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
              <div style={getIconBg(stat.color)}>
                {stat.icon}
              </div>
              <span className={'trend-badge ' + (stat.trend.startsWith('+') || stat.trend.startsWith('9') ? 'up' : 'down')}>
                {stat.trend}
              </span>
            </div>
            <div className="stat-label">{stat.label}</div>
            <div className="stat-value">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Recent Activity Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px', marginBottom: '32px' }}>
        {/* Recent Audit Logs */}
        <div className="glass-card">
          <div className="section-header" style={{ padding: '24px 24px 0 24px' }}>
            <div className="section-title">Recent Activity</div>
            <a href="/admin/audit" className="action-link">View All →</a>
          </div>
          <div>
            {data.recent_audit.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">📋</div>
                <div>No recent activity</div>
              </div>
            ) : (
              data.recent_audit.slice(0, 6).map((log: any, i: number) => (
                <div key={i} style={{
                  padding: '16px 24px',
                  borderBottom: '1px solid var(--border-color)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  transition: 'background 0.2s',
                  cursor: 'pointer',
                }}>
                  <div style={{
                    width: '40px',
                    height: '40px',
                    borderRadius: '10px',
                    background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(245, 158, 11, 0.1))',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '18px',
                    flexShrink: 0,
                  }}>
                    📌
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '2px' }}>
                      {log.action}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {log.detail || JSON.stringify(log.details)}
                    </div>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-faint)', flexShrink: 0 }}>
                    {log.created_at ? new Date(log.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <div className="section-title" style={{ marginBottom: '20px' }}>Quick Actions</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {quickActions.map((action) => (
              <a
                key={action.label}
                href={action.path}
                className="btn-secondary"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  textDecoration: 'none',
                  padding: '14px 16px',
                }}
              >
                <div style={getIconBg('#10b981')}>
                  {action.icon}
                </div>
                <span style={{ flex: 1 }}>{action.label}</span>
                <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" style={{ opacity: 0.5 }}>
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </a>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Errors */}
      {data.recent_errors.length > 0 && (
        <div className="glass-card">
          <div className="section-header" style={{ padding: '24px 24px 0 24px' }}>
            <div className="section-title">Recent Errors</div>
            <span className="status-badge danger">
              {data.recent_errors.length} Issues
            </span>
          </div>
          <table className="admin-table">
            <thead>
              <tr>
                <th>Status</th>
                <th>Endpoint</th>
                <th>Error Message</th>
                <th>Time</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_errors.slice(0, 5).map((err: any) => (
                <tr key={err.id}>
                  <td>
                    <span className={'status-badge ' + (err.acked ? 'warning' : 'danger')}>
                      {err.status}
                    </span>
                  </td>
                  <td style={{ fontFamily: 'monospace', fontSize: '12px', color: 'var(--accent-primary)' }}>
                    {err.method} {err.path}
                  </td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '13px' }}>{err.message}</td>
                  <td style={{ color: 'var(--text-faint)', fontSize: '12px' }}>
                    {err.created_at ? new Date(err.created_at).toLocaleString() : '-'}
                  </td>
                  <td>
                    <button className="btn-secondary" style={{ padding: '4px 12px', fontSize: '11px' }}>
                      Resolve
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}