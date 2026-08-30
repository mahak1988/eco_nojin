/**
 * SecurityAdvanced (Orchestrator)
 * =================================
 * Security Command Center dashboard.
 *
 * Key improvements from original (343 lines):
 * - React Query with refetchInterval (eliminated manual setInterval)
 * - Fixed stale closure bug (refetchInterval handled by React Query)
 * - useMemo for ALL derived statistics (O(n) operations)
 * - Type safety (no 'any')
 * - Data transformation moved to API layer
 * - Extracted 4 components (StatsCards, AuthTrendChart, EventDistributionChart, RecentEventsTable)
 * - 343 → ~80 lines orchestration (77% reduction)
 *
 * @module pages/admin/SecurityAdvanced
 */

import { useState } from 'react';
import { Shield, RefreshCw, Wifi, WifiOff, AlertTriangle } from 'lucide-react';

import { useSecurityEvents } from '../../features/security/hooks/useSecurityEvents';
import { useSecurityStats } from '../../features/security/hooks/useSecurityStats';
import { StatsCards } from '../../features/security/components/StatsCards';
import { AuthTrendChart } from '../../features/security/components/AuthTrendChart';
import { EventDistributionChart } from '../../features/security/components/EventDistributionChart';
import { RecentEventsTable } from '../../features/security/components/RecentEventsTable';

import './AdminTheme.css';
import './AdminPanelAdvanced.css';

export default function SecurityAdvanced() {
  const [autoRefresh, setAutoRefresh] = useState(true);

  // React Query hook (handles auto-refresh internally)
  const {
    events,
    isLoading,
    isError,
    error,
    refetch,
    dataUpdatedAt,
  } = useSecurityEvents({ autoRefresh });

  // Derived stats (memoized - computed only when events change)
  const stats = useSecurityStats(events);

  // Loading state
  if (isLoading) {
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
        <StatsCards stats={stats} isLoading={true} />
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="admin-page-container">
        <div className="alert-banner danger">
          <AlertTriangle size={24} />
          <div>
            <div style={{ fontWeight: 600 }}>Unable to load security data</div>
            <div style={{ fontSize: '13px', marginTop: '4px' }}>
              {error?.message || 'Unknown error'}
            </div>
          </div>
          <button
            className="refresh-btn"
            onClick={() => refetch()}
            style={{ marginLeft: 'auto' }}
          >
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
          <button className="refresh-btn" onClick={() => refetch()}>
            <RefreshCw size={16} /> Refresh
          </button>
          <div style={{ fontSize: '12px', color: 'var(--text-faint)' }}>
            Updated: {new Date(dataUpdatedAt).toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Stats */}
      <StatsCards stats={stats} />

      {/* Charts */}
      <div className="grid-2col">
        <AuthTrendChart data={stats.hourlyData} />
        <EventDistributionChart stats={stats} />
      </div>

      {/* Recent Events */}
      <RecentEventsTable events={events} />
    </div>
  );
}
