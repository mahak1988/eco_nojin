/**
 * FilterBar Component
 * ====================
 * @module features/content-studio/components
 */

import { Search } from 'lucide-react';
import type { ContentFilter } from '../types';
import { FILTER_OPTIONS } from '../constants/config';

interface FilterBarProps {
  filter: ContentFilter;
  onFilterChange: (filter: ContentFilter) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
}

export function FilterBar({
  filter,
  onFilterChange,
  searchQuery,
  onSearchChange,
}: FilterBarProps) {
  return (
    <div className="filter-bar">
      <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
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
          placeholder="Search content..."
          className="form-input"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          style={{ paddingLeft: '36px' }}
        />
      </div>
      <div style={{ display: 'flex', gap: '8px', marginLeft: 'auto' }}>
        {FILTER_OPTIONS.map((f) => (
          <button
            key={f}
            className={'filter-chip' + (filter === f ? ' active' : '')}
            onClick={() => onFilterChange(f)}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>
    </div>
  );
}
