import { useEffect, useState } from 'react';
import './AdminTheme.css';

const API_BASE = 'http://localhost:8000/api/v1';

interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export default function AdminUsers() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'active' | 'blocked'>('all');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const url = API_BASE + '/admin/users';
      const res = await fetch(url, {
        headers: { Authorization: 'Bearer ' + token },
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      const json = await res.json();
      setUsers(Array.isArray(json) ? json : json.users || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner" />
        <div style={{ color: 'var(--text-muted)' }}>Loading users...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="glass-card" style={{ padding: '40px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
        <h3 style={{ color: 'var(--accent-danger)', margin: '0 0 8px 0' }}>Unable to load users</h3>
        <p style={{ color: 'var(--text-muted)', margin: 0 }}>{error}</p>
      </div>
    );
  }

  const activeUsers = users.filter(u => u.is_active);
  const blockedUsers = users.filter(u => !u.is_active);
  const filteredUsers = filter === 'all' ? users : filter === 'active' ? activeUsers : blockedUsers;
  const searchedUsers = searchQuery
    ? filteredUsers.filter(u => u.email.toLowerCase().includes(searchQuery.toLowerCase()) || (u.full_name && u.full_name.toLowerCase().includes(searchQuery.toLowerCase())))
    : filteredUsers;

  return (
    <div>
      <div className="card-grid">
        <div className="stat-card">
          <div className="stat-label">Total Users</div>
          <div className="stat-value">{users.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Active</div>
          <div className="stat-value" style={{ color: 'var(--accent-primary)' }}>{activeUsers.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Blocked</div>
          <div className="stat-value" style={{ color: 'var(--accent-danger)' }}>{blockedUsers.length}</div>
        </div>
      </div>

      <div className="filter-bar">
        <input
          type="text"
          placeholder="Search by email or name..."
          className="form-input"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ flex: 1, maxWidth: '300px' }}
        />
        <div style={{ display: 'flex', gap: '8px', marginLeft: 'auto' }}>
          {(['all', 'active', 'blocked'] as const).map((f) => (
            <button key={f} className={'filter-chip' + (filter === f ? ' active' : '')} onClick={() => setFilter(f)}>
              {f.charAt(0).toUpperCase() + f.slice(1)} ({f === 'all' ? users.length : f === 'active' ? activeUsers.length : blockedUsers.length})
            </button>
          ))}
        </div>
      </div>

      <div className="glass-card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Joined</th>
            </tr>
          </thead>
          <tbody>
            {searchedUsers.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '60px 20px' }}>
                  <div style={{ fontSize: '48px', marginBottom: '16px', opacity: 0.3 }}>👥</div>
                  <div style={{ color: 'var(--text-muted)' }}>No users found</div>
                </td>
              </tr>
            ) : (
              searchedUsers.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        width: '36px', height: '36px', borderRadius: '10px',
                        background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: 'white', fontWeight: 700, fontSize: '13px',
                      }}>
                        {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{user.full_name || 'No name'}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-faint)' }}>ID: {user.id.substring(0, 8)}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ color: 'var(--text-secondary)', fontSize: '13px' }}>{user.email}</td>
                  <td><span className={'status-badge ' + (user.role === 'admin' ? 'warning' : 'info')}>{user.role}</span></td>
                  <td><span className={'status-badge ' + (user.is_active ? 'success' : 'danger')}>{user.is_active ? '✓ Active' : '✗ Blocked'}</span></td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '13px' }}>{user.created_at ? new Date(user.created_at).toLocaleDateString() : '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
