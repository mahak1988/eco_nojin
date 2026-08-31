/**
 * RecentEventsTable Component
 * =============================
 * @module features/security/components
 */

import { Eye, CheckCircle, XCircle } from 'lucide-react';
import type { SecurityEvent } from '../types';
import { CHART_CONFIG } from '../constants/config';
import { formatEventTime } from '../utils/formatters';

interface RecentEventsTableProps {
  events: SecurityEvent[];
}

export function RecentEventsTable({ events }: RecentEventsTableProps) {
  const recentEvents = events.slice(0, CHART_CONFIG.maxRecentEvents);
  const isSuccessful = (e: SecurityEvent) => e.type === 'Successful Login';

  return (
    <div className="chart-container">
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '20px',
        }}
      >
        <div className="chart-title" style={{ margin: 0 }}>
          <Eye size={20} />
          Recent Security Events
        </div>
        <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Showing latest {Math.min(CHART_CONFIG.maxRecentEvents, events.length)} of {events.length}{' '}
          events
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
            recentEvents.map((event) => (
              <tr key={event.id} className="transaction-row">
                <td>
                  <span className={`status-badge ${isSuccessful(event) ? 'success' : 'danger'}`}>
                    {isSuccessful(event) ? <CheckCircle size={14} /> : <XCircle size={14} />}
                    {isSuccessful(event) ? 'Success' : 'Failed'}
                  </span>
                </td>
                <td style={{ fontWeight: 500, color: 'var(--text-primary)' }}>{event.type}</td>
                <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>
                  {event.detail || '-'}
                </td>
                <td
                  style={{
                    fontFamily: 'monospace',
                    fontSize: '12px',
                    color: 'var(--text-muted)',
                  }}
                >
                  {event.ip_address || 'N/A'}
                </td>
                <td style={{ color: 'var(--text-faint)', fontSize: '12px' }}>
                  {formatEventTime(event.created_at)}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
