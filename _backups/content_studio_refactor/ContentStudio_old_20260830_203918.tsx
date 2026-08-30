import { useEffect, useState } from 'react';
import {
  FileText, Plus, Edit3, Trash2, Globe, Clock, CheckCircle,
  AlertCircle, Search, RefreshCw, Sparkles, Languages,
  History, Calendar, Eye, Send, XCircle, Zap
} from 'lucide-react';
import './AdminTheme.css';
import './AdminPanelAdvanced.css';

const API_BASE = 'http://localhost:8000/api/v1';

export default function ContentStudio() {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'published' | 'draft' | 'scheduled'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [generating, setGenerating] = useState(false);

  const fetchContent = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + '/admin/content', {
        headers: { Authorization: 'Bearer ' + token },
      });
      if (res.ok) {
        const data = await res.json();
        setItems(Array.isArray(data) ? data : data.items || []);
      }
    } catch (e) {
      console.error('Failed to fetch content:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchContent(); }, []);

  const publishItem = async (id: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + '/admin/content/' + id + '/publish', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token },
      });
      if (res.ok) fetchContent();
    } catch (e) {
      console.error('Failed to publish:', e);
    }
  };

  const deleteItem = async (id: string) => {
    if (!confirm('Are you sure you want to delete this content?')) return;
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + '/admin/content/' + id, {
        method: 'DELETE',
        headers: { Authorization: 'Bearer ' + token },
      });
      if (res.ok) fetchContent();
    } catch (e) {
      console.error('Failed to delete:', e);
    }
  };

  const generateDraft = async () => {
    setGenerating(true);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + '/admin/content/generate-draft', {
        method: 'POST',
        headers: {
          Authorization: 'Bearer ' + token,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic: 'Sustainable Farming', language: 'fa' }),
      });
      if (res.ok) {
        fetchContent();
        alert('AI draft generated successfully!');
      }
    } catch (e) {
      console.error('Failed to generate draft:', e);
    } finally {
      setGenerating(false);
    }
  };

  const translateItem = async (id: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + '/admin/content/' + id + '/translate', {
        method: 'POST',
        headers: {
          Authorization: 'Bearer ' + token,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ target_language: 'en' }),
      });
      if (res.ok) {
        alert('Translation initiated!');
        fetchContent();
      }
    } catch (e) {
      console.error('Failed to translate:', e);
    }
  };

  const published = items.filter(i => (i.status || '').toLowerCase() === 'published');
  const drafts = items.filter(i => (i.status || '').toLowerCase() === 'draft');
  const scheduled = items.filter(i => (i.status || '').toLowerCase() === 'scheduled');

  const filtered = filter === 'all' ? items :
    filter === 'published' ? published :
    filter === 'draft' ? drafts : scheduled;

  const searched = searchQuery
    ? filtered.filter(i =>
        (i.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (i.type || '').toLowerCase().includes(searchQuery.toLowerCase())
      )
    : filtered;

  if (loading) {
    return (
      <div className="admin-page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title"><FileText size={32} /> Content Studio</h1>
            <p className="page-subtitle">Loading content...</p>
          </div>
        </div>
        <div className="grid-4col">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="metric-card">
              <div className="skeleton skeleton-title"></div>
              <div className="skeleton skeleton-card"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="admin-page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <FileText size={32} style={{ color: 'var(--accent-primary)' }} />
            Content Studio
          </h1>
          <p className="page-subtitle">
            Create, manage, and publish platform content with AI assistance
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            className="btn-secondary"
            onClick={generateDraft}
            disabled={generating}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Sparkles size={16} />
            {generating ? 'Generating...' : 'AI Draft'}
          </button>
          <button className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Plus size={16} /> New Content
          </button>
          <button className="refresh-btn" onClick={fetchContent}>
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid-4col">
        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-info)' }}>
            <FileText size={28} />
          </div>
          <div className="metric-label">Total Content</div>
          <div className="metric-value">{items.length}</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-primary)' }}>
            <Globe size={28} />
          </div>
          <div className="metric-label">Published</div>
          <div className="metric-value" style={{ color: 'var(--accent-primary)' }}>{published.length}</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-secondary)' }}>
            <Edit3 size={28} />
          </div>
          <div className="metric-label">Drafts</div>
          <div className="metric-value" style={{ color: 'var(--accent-secondary)' }}>{drafts.length}</div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-purple)' }}>
            <Calendar size={28} />
          </div>
          <div className="metric-label">Scheduled</div>
          <div className="metric-value" style={{ color: 'var(--accent-purple)' }}>{scheduled.length}</div>
        </div>
      </div>

      {/* Filter + Search */}
      <div className="filter-bar">
        <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search content..."
            className="form-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: '36px' }}
          />
        </div>
        <div style={{ display: 'flex', gap: '8px', marginLeft: 'auto' }}>
          {(['all', 'published', 'draft', 'scheduled'] as const).map((f) => (
            <button
              key={f}
              className={'filter-chip' + (filter === f ? ' active' : '')}
              onClick={() => setFilter(f)}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Content Table */}
      <div className="chart-container">
        <table className="admin-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Type</th>
              <th>Status</th>
              <th>Author</th>
              <th>Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {searched.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <div className="empty-state-enhanced">
                    <div className="icon">📝</div>
                    <div className="title">No content found</div>
                    <div>Create your first content with AI assistance</div>
                  </div>
                </td>
              </tr>
            ) : (
              searched.map((item) => (
                <tr key={item.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        width: '36px', height: '36px', borderRadius: '8px',
                        background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: 'white', fontSize: '16px',
                      }}>
                        📄
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{item.title || 'Untitled'}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-faint)' }}>ID: {item.id?.substring(0, 8) || 'N/A'}</div>
                      </div>
                    </div>
                  </td>
                  <td><span className="status-badge info">{item.type || 'article'}</span></td>
                  <td>
                    <span className={'status-badge ' + (
                      (item.status || '').toLowerCase() === 'published' ? 'success' :
                      (item.status || '').toLowerCase() === 'draft' ? 'warning' : 'info'
                    )}>
                      {item.status || 'draft'}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{item.author || '-'}</td>
                  <td style={{ color: 'var(--text-muted)', fontSize: '12px' }}>
                    {item.updated_at ? new Date(item.updated_at).toLocaleDateString() : '-'}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button className="btn-secondary" style={{ padding: '6px 10px', fontSize: '11px' }} title="Edit">
                        <Edit3 size={12} />
                      </button>
                      <button className="btn-secondary" style={{ padding: '6px 10px', fontSize: '11px' }} title="View">
                        <Eye size={12} />
                      </button>
                      {item.status !== 'published' && (
                        <button className="btn-primary" style={{ padding: '6px 10px', fontSize: '11px' }} onClick={() => publishItem(item.id)} title="Publish">
                          <Send size={12} />
                        </button>
                      )}
                      <button className="btn-secondary" style={{ padding: '6px 10px', fontSize: '11px' }} onClick={() => translateItem(item.id)} title="Translate">
                        <Languages size={12} />
                      </button>
                      <button className="btn-danger" style={{ padding: '6px 10px', fontSize: '11px' }} onClick={() => deleteItem(item.id)} title="Delete">
                        <Trash2 size={12} />
                      </button>
                    </div>
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
