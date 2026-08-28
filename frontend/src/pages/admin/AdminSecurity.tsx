import { useEffect, useState } from 'react';

const API_BASE = 'http://localhost:8000/api/v1';

export default function AdminSecurity() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const res = await fetch(${API_BASE}/admin/security, {
          headers: { Authorization: Bearer  },
        });
        if (!res.ok) throw new Error(HTTP );
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

  if (loading) return <div style={{ padding: '40px' }}>Loading...</div>;
  if (error) return <div style={{ padding: '40px', color: '#dc2626' }}>Error: {error}</div>;

  const okEvents = events.filter(e => e.detail && e.detail.startsWith('ok'));
  const failedEvents = events.filter(e => e.detail && e.detail.startsWith('failed'));

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        <div style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <p style={{ color: '#6b7280', margin: 0 }}>Total Events</p>
          <p style={{ fontSize: '32px', fontWeight: 700, margin: '8px 0 0 0' }}>{events.length}</p>
        </div>
        <div style={{ background: '#ecfdf5', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <p style={{ color: '#047857', margin: 0 }}>Successful Logins</p>
          <p style={{ fontSize: '32px', fontWeight: 700, margin: '8px 0 0 0', color: '#047857' }}>{okEvents.length}</p>
        </div>
        <div style={{ background: '#fef2f2', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <p style={{ color: '#dc2626', margin: 0 }}>Failed Attempts</p>
          <p style={{ fontSize: '32px', fontWeight: 700, margin: '8px 0 0 0', color: '#dc2626' }}>{failedEvents.length}</p>
        </div>
      </div>

      <div style={{ background: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e5e7eb' }}>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>Authentication Events</h3>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ background: '#f9fafb' }}>
            <tr>
              <th style={{ padding: '12px 24px', textAlign: 'left', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase' }}>Status</th>
              <th style={{ padding: '12px 24px', textAlign: 'left', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase' }}>Details</th>
              <th style={{ padding: '12px 24px', textAlign: 'left', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase' }}>IP</th>
              <th style={{ padding: '12px 24px', textAlign: 'left', fontSize: '12px', fontWeight: 600, color: '#6b7280', textTransform: 'uppercase' }}>Time</th>
            </tr>
          </thead>
          <tbody>
            {events.length === 0 ? (
              <tr>
                <td colSpan={4} style={{ padding: '32px', textAlign: 'center', color: '#6b7280' }}>
                  No authentication events found
                </td>
              </tr>
            ) : (
              events.map((event, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                  <td style={{ padding: '16px 24px' }}>
                    <span style={{
                      padding: '4px 8px',
                      fontSize: '12px',
                      borderRadius: '4px',
                      background: event.detail && event.detail.startsWith('ok') ? '#d1fae5' : '#fee2e2',
                      color: event.detail && event.detail.startsWith('ok') ? '#047857' : '#dc2626',
                      fontWeight: 500,
                    }}>
                      {event.detail && event.detail.startsWith('ok') ? 'OK Success' : 'X Failed'}
                    </span>
                  </td>
                  <td style={{ padding: '16px 24px', fontSize: '14px' }}>{event.detail || '-'}</td>
                  <td style={{ padding: '16px 24px', fontSize: '14px', color: '#6b7280' }}>{event.ip_address || '-'}</td>
                  <td style={{ padding: '16px 24px', fontSize: '14px', color: '#9ca3af' }}>
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
