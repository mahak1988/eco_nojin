import { useEffect, useState } from 'react';
import { useLiveMetrics } from './live/useLiveMetrics';
import LiveCounter from './live/LiveCounter';
import LiveGauge from './live/LiveGauge';
import LiveFeed from './live/LiveFeed';
import LiveSparkline from './live/LiveSparkline';
import StatusBeacon from './live/StatusBeacon';
import LiveTicker from './live/LiveTicker';
import ProgressRing from './live/ProgressRing';
import {
  Users,
  ShoppingCart,
  DollarSign,
  Activity,
  Server,
  Shield,
  Zap,
  TrendingUp,
  Clock,
  Cpu,
  HardDrive,
  Globe,
  AlertCircle,
} from 'lucide-react';
import './AdminTheme.css';
import './AdminPanelAdvanced.css';

export default function LiveDashboard() {
  const { metrics, connected } = useLiveMetrics('/admin/overview');

  if (!metrics) {
    return (
      <div className="admin-page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">
              <Activity size={32} /> Live Command Center
            </h1>
            <p className="page-subtitle">Connecting to live data stream...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page-container">
      {/* Live Ticker at Top */}
      <LiveTicker />

      {/* Header with Status */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Activity size={32} style={{ color: 'var(--accent-primary)' }} />
            Live Command Center
          </h1>
          <p className="page-subtitle">Real-time monitoring and live metrics dashboard</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <StatusBeacon
            status={connected ? 'online' : 'offline'}
            label={connected ? 'Connected' : 'Disconnected'}
            size="md"
          />
          <div className="live-indicator">
            <span className="live-dot" />
            LIVE STREAM
          </div>
        </div>
      </div>

      {/* Live Counters Grid - 6 KPIs */}
      <div className="grid-3col">
        <LiveCounter
          value={metrics.active_users}
          label="Active Users"
          icon={<Users size={20} />}
          trend={12.5}
          color="primary"
          size="md"
        />
        <LiveCounter
          value={metrics.requests_per_second}
          label="Requests/sec"
          icon={<Zap size={20} />}
          trend={8.3}
          color="info"
          suffix=" r/s"
        />
        <LiveCounter
          value={metrics.revenue_today}
          label="Revenue Today"
          icon={<DollarSign size={20} />}
          trend={24.1}
          color="success"
          prefix=""
          suffix=" IRR"
        />
        <LiveCounter
          value={metrics.orders_today}
          label="Orders Today"
          icon={<ShoppingCart size={20} />}
          trend={15.7}
          color="purple"
        />
        <LiveCounter
          value={metrics.active_connections}
          label="Active Connections"
          icon={<Globe size={20} />}
          trend={-3.2}
          color="info"
        />
        <LiveCounter
          value={metrics.errors_last_hour}
          label="Errors (1h)"
          icon={<AlertCircle size={20} />}
          trend={-12.5}
          color="danger"
        />
      </div>

      {/* Gauges Row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '20px',
          marginBottom: '24px',
        }}
      >
        <div className="metric-card">
          <LiveGauge
            value={metrics.cpu_usage}
            label="CPU Usage"
            color={
              metrics.cpu_usage > 80 ? 'danger' : metrics.cpu_usage > 60 ? 'warning' : 'success'
            }
          />
          <LiveSparkline color="var(--accent-info)" autoUpdate />
        </div>

        <div className="metric-card">
          <LiveGauge
            value={metrics.memory_usage}
            label="Memory Usage"
            color={metrics.memory_usage > 85 ? 'danger' : 'primary'}
          />
          <LiveSparkline color="var(--accent-purple)" autoUpdate />
        </div>

        <div className="metric-card">
          <LiveGauge
            value={metrics.security_score}
            label="Security Score"
            color={
              metrics.security_score > 80
                ? 'success'
                : metrics.security_score > 50
                  ? 'warning'
                  : 'danger'
            }
          />
          <LiveSparkline color="var(--accent-primary)" autoUpdate />
        </div>

        <div className="metric-card">
          <LiveGauge
            value={metrics.pending_tasks}
            label="Pending Tasks"
            maxValue={50}
            color={metrics.pending_tasks > 30 ? 'warning' : 'success'}
            unit=""
          />
          <LiveSparkline color="var(--accent-secondary)" autoUpdate />
        </div>
      </div>

      {/* Progress Rings + Live Feed */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '24px' }}>
        {/* System Health */}
        <div className="chart-container">
          <div className="chart-title">
            <Server size={20} />
            System Health
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <ProgressRing progress={98} label="Uptime" color="var(--accent-primary)" />
            <ProgressRing progress={metrics.cpu_usage} label="CPU" color="var(--accent-info)" />
            <ProgressRing
              progress={metrics.memory_usage}
              label="Memory"
              color="var(--accent-purple)"
            />
            <ProgressRing progress={92} label="Network" color="var(--accent-secondary)" />
          </div>

          <div style={{ marginTop: '24px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <StatusBeacon status="online" label="API Gateway" size="sm" />
            <StatusBeacon status="online" label="Database" size="sm" />
            <StatusBeacon status="online" label="Cache" size="sm" />
            <StatusBeacon status="warning" label="CDN" size="sm" />
          </div>
        </div>

        {/* Live Activity Feed */}
        <LiveFeed maxItems={8} pollInterval={4000} />
      </div>

      {/* Footer Info */}
      <div
        style={{
          marginTop: '24px',
          padding: '16px 24px',
          background: 'var(--bg-card)',
          borderRadius: '12px',
          border: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div style={{ display: 'flex', gap: '24px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={16} style={{ color: 'var(--text-muted)' }} />
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Last update: {new Date().toLocaleTimeString()}
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={16} style={{ color: 'var(--accent-primary)' }} />
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Update interval: 3s
            </span>
          </div>
        </div>
        <div
          style={{
            fontSize: '11px',
            color: 'var(--text-faint)',
            letterSpacing: '1px',
            textTransform: 'uppercase',
          }}
        >
          Real-Time Dashboard • Phase 3
        </div>
      </div>
    </div>
  );
}
