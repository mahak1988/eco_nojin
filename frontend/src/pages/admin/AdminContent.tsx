import { useState } from 'react';
import './AdminTheme.css';

export default function AdminContent() {
  const [filter, setFilter] = useState<'all' | 'published' | 'draft' | 'pending'>('all');

  const contentItems = [
    {
      id: 1,
      title: 'Sustainable Farming Practices',
      type: 'article',
      status: 'published',
      author: 'admin',
      updated: '2026-08-27',
    },
    {
      id: 2,
      title: 'Organic Fertilizer Guide',
      type: 'article',
      status: 'draft',
      author: 'editor',
      updated: '2026-08-26',
    },
    {
      id: 3,
      title: 'Water Conservation Tips',
      type: 'article',
      status: 'published',
      author: 'admin',
      updated: '2026-08-25',
    },
    {
      id: 4,
      title: 'Soil Health Analysis',
      type: 'report',
      status: 'pending',
      author: 'analyst',
      updated: '2026-08-24',
    },
    {
      id: 5,
      title: 'Carbon Credit Explained',
      type: 'article',
      status: 'published',
      author: 'admin',
      updated: '2026-08-23',
    },
  ];

  const filteredContent =
    filter === 'all' ? contentItems : contentItems.filter((c) => c.status === filter);

  return (
    <div>
      <div className="info-banner">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2 style={{ margin: '0 0 8px 0', fontSize: '28px', fontWeight: 800 }}>
              Content Management
            </h2>
            <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '14px' }}>
              Manage articles, reports, and platform content
            </p>
          </div>
          <button className="btn-primary">+ New Content</button>
        </div>
      </div>

      <div className="card-grid">
        <div className="stat-card">
          <div className="stat-label">Total Content</div>
          <div className="stat-value">{contentItems.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Published</div>
          <div className="stat-value" style={{ color: 'var(--accent-primary)' }}>
            {contentItems.filter((c) => c.status === 'published').length}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Drafts</div>
          <div className="stat-value">
            {contentItems.filter((c) => c.status === 'draft').length}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Pending Review</div>
          <div className="stat-value" style={{ color: 'var(--accent-secondary)' }}>
            {contentItems.filter((c) => c.status === 'pending').length}
          </div>
        </div>
      </div>

      <div className="filter-bar">
        <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginRight: '8px' }}>
          Filter:
        </div>
        {(['all', 'published', 'draft', 'pending'] as const).map((f) => (
          <button
            key={f}
            className={'filter-chip' + (filter === f ? ' active' : '')}
            onClick={() => setFilter(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      <div className="glass-card">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Type</th>
              <th>Author</th>
              <th>Status</th>
              <th>Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredContent.map((item) => (
              <tr key={item.id}>
                <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.title}</td>
                <td>
                  <span className="status-badge info">{item.type}</span>
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>{item.author}</td>
                <td>
                  <span
                    className={
                      'status-badge ' +
                      (item.status === 'published'
                        ? 'success'
                        : item.status === 'draft'
                          ? 'info'
                          : 'warning')
                    }
                  >
                    {item.status}
                  </span>
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: '13px' }}>{item.updated}</td>
                <td>
                  <button
                    className="btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '11px' }}
                  >
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
