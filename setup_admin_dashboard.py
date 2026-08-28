import os
from pathlib import Path

ROOT = Path(r"D:\eco_nojin\frontend")
ADMIN_DIR = ROOT / "src" / "pages" / "admin"

print("=" * 80)
print("SETTING UP ADMIN DASHBOARD")
print("=" * 80)

# Create admin directory
ADMIN_DIR.mkdir(parents=True, exist_ok=True)
print(f"[OK] Created directory: {ADMIN_DIR}")

# =========================================================================
# FILE 1: AdminLayout.tsx
# =========================================================================
layout_code = r"""import { ReactNode } from 'react';
import { Link, useLocation } from 'react-router-dom';

interface AdminLayoutProps {
  children: ReactNode;
}

export default function AdminLayout({ children }: AdminLayoutProps) {
  const location = useLocation();
  
  const navItems = [
    { path: '/admin', label: 'Overview', icon: 'chart' },
    { path: '/admin/users', label: 'Users', icon: 'users' },
    { path: '/admin/audit', label: 'Audit Logs', icon: 'list' },
    { path: '/admin/security', label: 'Security', icon: 'shield' },
    { path: '/admin/errors', label: 'Errors', icon: 'alert' },
    { path: '/admin/content', label: 'Content', icon: 'file' },
    { path: '/admin/settings', label: 'Settings', icon: 'settings' },
  ];
  
  const getIcon = (name: string) => {
    const icons: Record<string, string> = {
      chart: 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z',
      users: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z',
      list: 'M4 6h16M4 10h16M4 14h16M4 18h16',
      shield: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
      alert: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z',
      file: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
      settings: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z',
    };
    return icons[name] || icons.chart;
  };
  
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: '#f9fafb' }}>
      <aside style={{ width: '260px', background: 'white', boxShadow: '2px 0 8px rgba(0,0,0,0.05)' }}>
        <div style={{ padding: '24px', borderBottom: '1px solid #e5e7eb' }}>
          <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700, color: '#047857' }}>
            Eco Nojin Admin
          </h2>
        </div>
        <nav style={{ padding: '16px 0' }}>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '12px 24px',
                  margin: '2px 0',
                  textDecoration: 'none',
                  color: isActive ? '#047857' : '#4b5563',
                  background: isActive ? '#ecfdf5' : 'transparent',
                  borderRight: isActive ? '4px solid #047857' : '4px solid transparent',
                  fontSize: '14px',
                  fontWeight: 500,
                  transition: 'all 0.2s',
                }}
              >
                <svg style={{ width: '20px', height: '20px', marginRight: '12px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={getIcon(item.icon)} />
                </svg>
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      
      <main style={{ flex: 1, overflow: 'auto' }}>
        <header style={{ background: 'white', borderBottom: '1px solid #e5e7eb', padding: '16px 32px' }}>
          <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 600, color: '#111827' }}>
            {navItems.find(i => i.path === location.pathname)?.label || 'Admin'}
          </h1>
        </header>
        <div style={{ padding: '32px' }}>
          {children}
        </div>
      </main>
    </div>
  );
}
"""

(ADMIN_DIR / "AdminLayout.tsx").write_text(layout_code, encoding='utf-8')
print("[OK] Created AdminLayout.tsx")

# =========================================================================
# FILE 2: AdminOverview.tsx
# =========================================================================
overview_code = r"""import { useEffect, useState } from 'react';

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
        const res = await fetch(${API_BASE}/admin/overview, {
          headers: { Authorization: Bearer  },
        });
        if (!res.ok) throw new Error(HTTP );
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
    return <div style={{ padding: '40px', textAlign: 'center' }}>Loading overview...</div>;
  }
  if (error) {
    return (
      <div style={{ padding: '40px', color: '#dc2626', background: '#fee2e2', borderRadius: '8px' }}>
        Error loading overview: {error}
      </div>
    );
  }
  if (!data) return null;

  const stats = [
    { label: 'Users', value: data.counts.users, icon: 'users', color: '#3b82f6' },
    { label: 'Farms', value: data.counts.farms, icon: 'farm', color: '#10b981' },
    { label: 'Audit Logs', value: data.counts.audit_entries, icon: 'list', color: '#8b5cf6' },
    { label: 'Errors (Open)', value: data.counts.errors_open, icon: 'alert', color: '#ef4444' },
    { label: 'Content', value: data.counts.content_total, icon: 'file', color: '#f59e0b' },
    { label: 'Uptime', value: ${(data.uptime_seconds / 3600).toFixed(1)}h, icon: 'clock', color: '#6b7280' },
  ];

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px', marginBottom: '32px' }}>
        {stats.map((stat) => (
          <div key={stat.label} style={{ background: 'white', borderRadius: '12px', padding: '24px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>{stat.label}</p>
                <p style={{ fontSize: '32px', fontWeight: 700, margin: '8px 0 0 0', color: stat.color }}>
                  {stat.value}
                </p>
              </div>
              <div style={{ fontSize: '40px', opacity: 0.2 }}>{stat.icon === 'users' ? 'U' : stat.icon === 'farm' ? 'F' : stat.icon === 'list' ? 'L' : stat.icon === 'alert' ? 'A' : stat.icon === 'file' ? 'D' : 'T'}</div>
            </div>
          </div>
        ))}
      </div>

      <div style={{ background: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)', marginBottom: '24px' }}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e5e7eb' }}>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>Recent Audit Logs</h3>
        </div>
        <div>
          {data.recent_audit.length === 0 ? (
            <p style={{ padding: '24px', color: '#6b7280', margin: 0 }}>No recent audit logs</p>
          ) : (
            data.recent_audit.slice(0, 10).map((log: any, i: number) => (
              <div key={i} style={{ padding: '16px 24px', borderBottom: '1px solid #f3f4f6', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <p style={{ fontWeight: 500, margin: 0 }}>{log.action}</p>
                  <p style={{ fontSize: '13px', color: '#6b7280', margin: '4px 0 0 0' }}>{log.detail || JSON.stringify(log.details)}</p>
                </div>
                <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                  {log.created_at ? new Date(log.created_at).toLocaleString() : ''}
                </span>
              </div>
            ))
          )}
        </div>
      </div>

      {data.recent_errors.length > 0 && (
        <div style={{ background: 'white', borderRadius: '12px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <div style={{ padding: '20px 24px', borderBottom: '1px solid #e5e7eb' }}>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>Recent Errors</h3>
          </div>
          <div>
            {data.recent_errors.map((err: any) => (
              <div key={err.id} style={{ padding: '16px 24px', borderBottom: '1px solid #f3f4f6' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <p style={{ fontWeight: 500, margin: 0 }}>{err.method} {err.path}</p>
                    <p style={{ fontSize: '13px', color: '#6b7280', margin: '4px 0 0 0' }}>{err.message}</p>
                  </div>
                  <span style={{
                    padding: '4px 8px',
                    fontSize: '12px',
                    borderRadius: '4px',
                    background: err.acked ? '#f3f4f6' : '#fee2e2',
                    color: err.acked ? '#6b7280' : '#dc2626',
                    fontWeight: 500,
                  }}>
                    {err.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
"""

(ADMIN_DIR / "AdminOverview.tsx").write_text(overview_code, encoding='utf-8')
print("[OK] Created AdminOverview.tsx")

# =========================================================================
# FILE 3: AdminSecurity.tsx
# =========================================================================
security_code = r"""import { useEffect, useState } from 'react';

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
"""

(ADMIN_DIR / "AdminSecurity.tsx").write_text(security_code, encoding='utf-8')
print("[OK] Created AdminSecurity.tsx")

# =========================================================================
# FILE 4: Index file
# =========================================================================
index_code = """export { default as AdminLayout } from './AdminLayout';
export { default as AdminOverview } from './AdminOverview';
export { default as AdminSecurity } from './AdminSecurity';
"""

(ADMIN_DIR / "index.ts").write_text(index_code, encoding='utf-8')
print("[OK] Created index.ts")

print("")
print("=" * 80)
print("ADMIN DASHBOARD SETUP COMPLETE!")
print("=" * 80)
print("")
print("Files created:")
for f in ADMIN_DIR.glob("*"):
    print(f"  - {f.relative_to(ROOT)}")
print("")
print("Next step: Add admin routes to App.tsx")
print("  Run this command:")
print("  python D:\\eco_nojin\\add_admin_routes.py")
