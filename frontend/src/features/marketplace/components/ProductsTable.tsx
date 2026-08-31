/**
 * ProductsTable Component
 * =========================
 * @module features/marketplace/components
 */

import { Package, Search, Eye } from 'lucide-react';
import type { Product } from '../types';
import { LIMITS } from '../constants/config';
import { formatCurrency, truncateId, safeString } from '../utils/formatters';

interface ProductsTableProps {
  products: Product[];
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export function ProductsTable({ products, searchQuery, onSearchChange }: ProductsTableProps) {
  // Filter based on search query
  const filteredProducts = searchQuery
    ? products.filter((p) => {
        const q = searchQuery.toLowerCase();
        return (
          (p.name || '').toLowerCase().includes(q) || (p.producer || '').toLowerCase().includes(q)
        );
      })
    : products;

  const displayedProducts = filteredProducts.slice(0, LIMITS.productsTableDisplay);

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
          <Package size={20} />
          Products Catalog
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{ position: 'relative' }}>
            <Search
              size={16}
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-muted)',
              }}
            />
            <input
              type="text"
              placeholder="Search products..."
              className="form-input"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              style={{ paddingLeft: '36px', width: '250px' }}
            />
          </div>
        </div>
      </div>

      <table className="admin-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Producer</th>
            <th>Price</th>
            <th>Stock</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {displayedProducts.length === 0 ? (
            <tr>
              <td colSpan={6}>
                <div className="empty-state-enhanced">
                  <div className="icon">📦</div>
                  <div className="title">No products found</div>
                  <div>{searchQuery ? 'Try a different search' : 'No products in catalog'}</div>
                </div>
              </td>
            </tr>
          ) : (
            displayedProducts.map((product, i) => (
              <tr key={product.id || i}>
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
                        width: '40px',
                        height: '40px',
                        borderRadius: '10px',
                        background:
                          'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontSize: '18px',
                      }}
                    >
                      🌾
                    </div>
                    <div>
                      <div
                        style={{
                          fontWeight: 600,
                          color: 'var(--text-primary)',
                        }}
                      >
                        {safeString(product.name, 'Unnamed')}
                      </div>
                      <div
                        style={{
                          fontSize: '12px',
                          color: 'var(--text-faint)',
                        }}
                      >
                        ID: {truncateId(product.id)}
                      </div>
                    </div>
                  </div>
                </td>
                <td style={{ color: 'var(--text-secondary)' }}>{safeString(product.producer)}</td>
                <td
                  style={{
                    fontWeight: 600,
                    color: 'var(--accent-primary)',
                  }}
                >
                  {formatCurrency(product.price || 0)} IRR
                </td>
                <td>{product.stock !== undefined ? product.stock : '-'}</td>
                <td>
                  <span className="status-badge success">Active</span>
                </td>
                <td>
                  <button
                    className="btn-secondary"
                    style={{ padding: '6px 12px', fontSize: '11px' }}
                  >
                    <Eye size={12} style={{ marginRight: '4px' }} /> Trace
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
