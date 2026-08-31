import { useEffect, useState } from 'react';
import {
  Bot,
  Power,
  Activity,
  Clock,
  Zap,
  RefreshCw,
  CheckCircle,
  XCircle,
  Settings,
  AlertCircle,
} from 'lucide-react';
import './AdminTheme.css';
import './AdminPanelAdvanced.css';

const API_BASE = 'http://localhost:8000/api/v1';

export default function BotsManagement() {
  const [bots, setBots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchBots = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + '/admin/bots', {
        headers: { Authorization: 'Bearer ' + token },
      });
      if (res.ok) {
        const data = await res.json();
        setBots(Array.isArray(data) ? data : data.bots || []);
      }
    } catch (e) {
      console.error('Failed to fetch bots:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBots();
  }, []);

  const toggleBot = async (key: string, currentStatus: boolean) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + '/admin/bots/' + key + '/toggle', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token },
      });
      if (res.ok) fetchBots();
    } catch (e) {
      console.error('Failed to toggle bot:', e);
    }
  };

  if (loading) {
    return (
      <div className="admin-page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">
              <Bot size={32} /> Bots Management
            </h1>
            <p className="page-subtitle">Loading bots...</p>
          </div>
        </div>
        <div className="grid-3col">
          {[1, 2, 3].map((i) => (
            <div key={i} className="metric-card">
              <div className="skeleton skeleton-card"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const activeBots = bots.filter((b) => b.active || b.enabled);
  const inactiveBots = bots.filter((b) => !(b.active || b.enabled));

  return (
    <div className="admin-page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Bot size={32} style={{ color: 'var(--accent-primary)' }} />
            Bots Management
          </h1>
          <p className="page-subtitle">Monitor and control platform automation bots</p>
        </div>
        <button className="refresh-btn" onClick={fetchBots}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid-3col">
        <div className="metric-card">
          <div
            className="metric-icon"
            style={{ background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-info)' }}
          >
            <Bot size={28} />
          </div>
          <div className="metric-label">Total Bots</div>
          <div className="metric-value">{bots.length}</div>
        </div>
        <div className="metric-card">
          <div
            className="metric-icon"
            style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-primary)' }}
          >
            <CheckCircle size={28} />
          </div>
          <div className="metric-label">Active</div>
          <div className="metric-value" style={{ color: 'var(--accent-primary)' }}>
            {activeBots.length}
          </div>
        </div>
        <div className="metric-card">
          <div
            className="metric-icon"
            style={{ background: 'rgba(239, 68, 68, 0.15)', color: 'var(--accent-danger)' }}
          >
            <XCircle size={28} />
          </div>
          <div className="metric-label">Inactive</div>
          <div className="metric-value" style={{ color: 'var(--accent-danger)' }}>
            {inactiveBots.length}
          </div>
        </div>
      </div>

      {/* Bots Grid */}
      <div className="grid-2col">
        {bots.length === 0 ? (
          <div className="chart-container" style={{ gridColumn: '1 / -1' }}>
            <div className="empty-state-enhanced">
              <div className="icon">🤖</div>
              <div className="title">No bots configured</div>
              <div>Bots will appear here when configured in the system</div>
            </div>
          </div>
        ) : (
          bots.map((bot, i) => {
            const isActive = bot.active || bot.enabled;
            return (
              <div key={bot.key || bot.id || i} className="metric-card">
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '16px',
                  }}
                >
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <div
                      style={{
                        width: '56px',
                        height: '56px',
                        borderRadius: '14px',
                        background: isActive
                          ? 'linear-gradient(135deg, #10b981, #059669)'
                          : 'var(--border-color)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        transition: 'all 0.3s',
                      }}
                    >
                      <Bot size={28} />
                    </div>
                    <div>
                      <div
                        style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '16px' }}
                      >
                        {bot.name || bot.key || 'Bot ' + (i + 1)}
                      </div>
                      <div
                        style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}
                      >
                        {bot.description || 'Automation bot'}
                      </div>
                    </div>
                  </div>
                  <div
                    className={'toggle-switch' + (isActive ? ' active' : '')}
                    onClick={() => toggleBot(bot.key || bot.id, isActive)}
                  />
                </div>

                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '1fr 1fr',
                    gap: '12px',
                    marginTop: '16px',
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontSize: '11px',
                        color: 'var(--text-faint)',
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                        marginBottom: '4px',
                      }}
                    >
                      Status
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <span className={'status-dot ' + (isActive ? 'online' : 'offline')}></span>
                      <span
                        style={{
                          color: isActive ? 'var(--accent-primary)' : 'var(--accent-danger)',
                          fontWeight: 600,
                          fontSize: '13px',
                        }}
                      >
                        {isActive ? 'Running' : 'Stopped'}
                      </span>
                    </div>
                  </div>
                  <div>
                    <div
                      style={{
                        fontSize: '11px',
                        color: 'var(--text-faint)',
                        textTransform: 'uppercase',
                        letterSpacing: '1px',
                        marginBottom: '4px',
                      }}
                    >
                      Last Run
                    </div>
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                      {bot.last_run ? new Date(bot.last_run).toLocaleString() : 'Never'}
                    </div>
                  </div>
                </div>

                <div style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
                  <button
                    className="btn-secondary"
                    style={{
                      flex: 1,
                      padding: '8px',
                      fontSize: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                    }}
                  >
                    <Activity size={14} /> Logs
                  </button>
                  <button
                    className="btn-secondary"
                    style={{
                      flex: 1,
                      padding: '8px',
                      fontSize: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: '6px',
                    }}
                  >
                    <Settings size={14} /> Config
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
