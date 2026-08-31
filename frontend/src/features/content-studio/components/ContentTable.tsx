/**
 * ContentTable Component
 * ========================
 * @module features/content-studio/components
 */

import { Edit3, Eye, Send, Languages, Trash2 } from 'lucide-react';
import type { ContentItem } from '../types';
import { truncateId, formatDate, normalizeStatus, getStatusBadgeClass } from '../utils/formatters';

interface ContentTableProps {
  items: ContentItem[];
  onPublish: (id: string) => void;
  onDelete: (id: string) => void;
  onTranslate: (id: string) => void;
  isPublishing?: boolean;
  isDeleting?: boolean;
  isTranslating?: boolean;
}

export function ContentTable({
  items,
  onPublish,
  onDelete,
  onTranslate,
  isPublishing,
  isDeleting,
  isTranslating,
}: ContentTableProps) {
  return (
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
          {items.length === 0 ? (
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
            items.map((item) => (
              <tr key={item.id}>
                <td>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                    }}
                  >
                    <div
                      style={{
                        width: '36px',
                        height: '36px',
                        borderRadius: '8px',
                        background:
                          'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontSize: '16px',
                      }}
                    >
                      📄
                    </div>
                    <div>
                      <div
                        style={{
                          fontWeight: 600,
                          color: 'var(--text-primary)',
                        }}
                      >
                        {item.title || 'Untitled'}
                      </div>
                      <div
                        style={{
                          fontSize: '11px',
                          color: 'var(--text-faint)',
                        }}
                      >
                        ID: {truncateId(item.id)}
                      </div>
                    </div>
                  </div>
                </td>
                <td>
                  <span className="status-badge info">{item.type || 'article'}</span>
                </td>
                <td>
                  <span className={`status-badge ${getStatusBadgeClass(item.status)}`}>
                    {item.status || 'draft'}
                  </span>
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>{item.author || '-'}</td>
                <td
                  style={{
                    color: 'var(--text-muted)',
                    fontSize: '12px',
                  }}
                >
                  {formatDate(item.updated_at)}
                </td>
                <td>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button
                      className="btn-secondary"
                      style={{ padding: '6px 10px', fontSize: '11px' }}
                      title="Edit"
                    >
                      <Edit3 size={12} />
                    </button>
                    <button
                      className="btn-secondary"
                      style={{ padding: '6px 10px', fontSize: '11px' }}
                      title="View"
                    >
                      <Eye size={12} />
                    </button>
                    {normalizeStatus(item.status) !== 'published' && (
                      <button
                        className="btn-primary"
                        style={{ padding: '6px 10px', fontSize: '11px' }}
                        onClick={() => onPublish(item.id)}
                        disabled={isPublishing}
                        title="Publish"
                      >
                        <Send size={12} />
                      </button>
                    )}
                    <button
                      className="btn-secondary"
                      style={{ padding: '6px 10px', fontSize: '11px' }}
                      onClick={() => onTranslate(item.id)}
                      disabled={isTranslating}
                      title="Translate"
                    >
                      <Languages size={12} />
                    </button>
                    <button
                      className="btn-danger"
                      style={{ padding: '6px 10px', fontSize: '11px' }}
                      onClick={() => onDelete(item.id)}
                      disabled={isDeleting}
                      title="Delete"
                    >
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
  );
}
