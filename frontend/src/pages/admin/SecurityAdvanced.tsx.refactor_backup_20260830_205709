import { useEffect, useState, useRef } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  Shield, AlertTriangle, Lock, Unlock, Eye, EyeOff,
  TrendingUp, TrendingDown, Activity, Zap, CheckCircle,
  XCircle, RefreshCw, Fingerprint, Wifi, WifiOff
} from 'lucide-react';
import './AdminTheme.css';
import './AdminPanelAdvanced.css';

const API_BASE = 'http://localhost:8000/api/v1';

interface SecurityEvent {
  id: string;
  type: string;
  detail: string;
  ip_address: string;
  created_at: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export default function SecurityAdvanced() {
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [autoRefresh, setAutoRefresh] = useState(true);
  const intervalRef = useRef<number | null>(null);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + '/admin/security', {
        headers: { Authorization: 'Bearer ' + token },
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const json = await res.json();
      const evts = (json.events || []).map((e: any, i: number) => ({
        ...e,
        id: e.id || 'evt-' + i,
        severity: e.detail?.startsWith('failed') ? 'high' : 'low',
        type: e.detail?.startsWith('failed') ? 'Failed Login' : 'Successful Login',
      }));
      setEvents(evts);
      setLastUpdate(new Date());
      setError(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = window.setInterval(fetchData, 10000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [autoRefresh]);

  const okEvents = events.filter(e => e.type === 'Successful Login');
  const failedEvents = events.filter(e => e.type === 'Failed Login');
  const successRate = events.length > 0 ? ((okEvents.length / events.length) * 100).toFixed(1) : '0';
  const securityScore = Math.min(100, Math.max(0, 100 - (failedEvents.length * 5)));

  // Group events by hour for chart
  const hourlyData = Array.from({ length: 24 }, (_, i) => {
    const hour = (new Date().getHours() - 23 + i + 24) % 24;
    const hourEvents = events.filter(e => {
      if (!e.created_at) return false;
      return new Date(e.created_at).getHours() === hour;
    });
    return {
      hour: hour.toString().padStart(2, '0') + ':00',
      success: hourEvents.filter(e => e.type === 'Successful Login').length,
      failed: hourEvents.filter(e => e.type === 'Failed Login').length,
    };
  });

  // Unique IPs that failed
  const uniqueFailedIPs = new Set(failedEvents.map(e => e.ip_address).filter(Boolean));

  if (loading) {
    return (
      <div className="admin-page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">
              <Shield size={32} /> Security Command Center
            </h1>
            <p className="page-subtitle">Loading security intelligence...</p>
          </div>
        </div>
        <div className="grid-4col">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="metric-card">
              <div className="skeleton skeleton-title"></div>
              <div className="skeleton skeleton-text"></div>
              <div className="skeleton skeleton-card"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="admin-page-container">
        <div className="alert-banner danger">
          <AlertTriangle size={24} />
          <div>
            <div style={{ fontWeight: 600 }}>Unable to load security data</div>
            <div style={{ fontSize: '13px', marginTop: '4px' }}>{error}</div>
          </div>
          <button className="refresh-btn" onClick={fetchData} style={{ marginLeft: 'auto' }}>
            <RefreshCw size={16} /> Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page-container">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Shield size={32} style={{ color: 'var(--accent-primary)' }} />
            Security Command Center
          </h1>
          <p className="page-subtitle">
            Real-time threat monitoring and authentication intelligence
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div className="live-indicator">LIVE</div>
          <button
            className="refresh-btn"
            onClick={() => setAutoRefresh(!autoRefresh)}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            {autoRefresh ? <Wifi size={16} /> : <WifiOff size={16} />}
            Auto-refresh {autoRefresh ? 'ON' : 'OFF'}
          </button>
          <button className="refresh-btn" onClick={fetchData}>
            <RefreshCw size={16} /> Refresh
          </button>
          <div style={{ fontSize: '12px', color: 'var(--text-faint)' }}>
            Updated: {lastUpdate.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid-4col">
        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-info)' }}>
            <Activity size={28} />
          </div>
          <div className="metric-label">Total Events</div>
          <div className="metric-value">{events.length}</div>
          <div className="metric-change positive">
            <TrendingUp size={12} /> Live
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-primary)' }}>
            <CheckCircle size={28} />
          </div>
          <div className="metric-label">Success Rate</div>
          <div className="metric-value" style={{ color: 'var(--accent-primary)' }}>{successRate}%</div>
          <div className="metric-change positive">
            <TrendingUp size={12} /> {okEvents.length} successful
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-danger)' }}>
            <AlertTriangle size={28} />
          </div>
          <div className="metric-label">Failed Attempts</div>
          <div className="metric-value" style={{ color: 'var(--accent-danger)' }}>{failedEvents.length}</div>
          <div className="metric-change negative">
            <TrendingDown size={12} /> {uniqueFailedIPs.size} unique IPs
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-secondary)' }}>
            <Shield size={28} />
          </div>
          <div className="metric-label">Security Score</div>
          <div className="metric-value" style={{
            color: securityScore > 80 ? 'var(--accent-primary)' : securityScore > 50 ? 'var(--accent-secondary)' : 'var(--accent-danger)'
          }}>
            {securityScore}
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: securityScore + '%' }} />
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid-2col">
        {/* Authentication Trend */}
        <div className="chart-container">
          <div className="chart-title">
            <Activity size={20} />
            Authentication Trend (24h)
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={hourlyData}>
              <defs>
                <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
                </linearGradient>
                <linearGradient id="colorFailed" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
              <XAxis dataKey="hour" stroke="var(--text-muted)" fontSize={11} />
              <YAxis stroke="var(--text-muted)" fontSize={11} />
              <Tooltip
                contentStyle={{
                  background: 'var(--bg-card-solid)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                }}
              />
              <Legend />
              <Area type="monotone" dataKey="success" stroke="#10b981" fillOpacity={1} fill="url(#colorSuccess)" name="Successful" />
              <Area type="monotone" dataKey="failed" stroke="#ef4444" fillOpacity={1} fill="url(#colorFailed)" name="Failed" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Threat Distribution */}
        <div className="chart-container">
          <div className="chart-title">
            <Zap size={20} />
            Event Distribution
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={[
              { name: 'Success', value: okEvents.length, fill: '#10b981' },
              { name: 'Failed', value: failedEvents.length, fill: '#ef4444' },
              { name: 'Unique IPs', value: uniqueFailedIPs.size, fill: '#f59e0b' },
            ]}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: 'var(--bg-card-solid)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                }}
              />
              <Bar dataKey="value" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Events */}
      <div className="chart-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div className="chart-title" style={{ margin: 0 }}>
            <Eye size={20} />
            Recent Security Events
          </div>
          <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            Showing latest {Math.min(10, events.length)} of {events.length} events
          </span>
        </div>

        <table className="admin-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Type</th>
              <th>Details</th>
              <th>IP Address</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 ? (
              <tr>
                <td colSpan={5}>
                  <div className="empty-state-enhanced">
                    <div className="icon">🛡️</div>
                    <div className="title">No Security Events</div>
                    <div>No authentication events recorded yet</div>
                  </div>
                </td>
              </tr>
            ) : (
              events.slice(0, 10).map((event) => (
                <tr key={event.id} className="transaction-row">
                  <td>
                    <span className={'status-badge ' + (event.type === 'Successful Login' ? 'success' : 'danger')}>
                      {event.type === 'Successful Login' ? <CheckCircle size={14} /> : <XCircle size={14} />}
                      {event.type === 'Successful Login' ? 'Success' : 'Failed'}
                    </span>
                  </td>
                  <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{event.type}</td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{event.detail || '-'}</td>
                  <td style={{ fontFamily: 'monospace', fontSize: '12px', color: 'var(--text-muted)' }}>
                    {event.ip_address || 'N/A'}
                  </td>
                  <td style={{ color: 'var(--text-faint)', fontSize: '12px' }}>
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
