/**
 * ContentStudio (Orchestrator)
 * ==============================
 * Content management dashboard with AI assistance.
 *
 * Key improvements from original (322 lines):
 * - React Query for data fetching (useQuery)
 * - 4 separate useMutation hooks (publish, delete, generate, translate)
 * - useMemo for derived data (filter, search)
 * - Type safety (no 'any')
 * - Extracted 3 components (StatsCards, FilterBar, ContentTable)
 * - 322 → ~80 lines orchestration (75% reduction)
 *
 * @module pages/admin/ContentStudio
 */

import { useState, useMemo } from 'react';
import { FileText, Plus, Sparkles, RefreshCw } from 'lucide-react';

import { useContentItems } from '../../features/content-studio/hooks/useContentItems';
import { usePublishItem } from '../../features/content-studio/hooks/usePublishItem';
import { useDeleteItem } from '../../features/content-studio/hooks/useDeleteItem';
import { useGenerateDraft } from '../../features/content-studio/hooks/useGenerateDraft';
import { useTranslateItem } from '../../features/content-studio/hooks/useTranslateItem';
import { StatsCards } from '../../features/content-studio/components/StatsCards';
import { FilterBar } from '../../features/content-studio/components/FilterBar';
import { ContentTable } from '../../features/content-studio/components/ContentTable';
import { normalizeStatus } from '../../features/content-studio/utils/formatters';
import {
  DEFAULT_TOPIC,
  DEFAULT_LANGUAGE,
  DEFAULT_TRANSLATION_TARGET,
} from '../../features/content-studio/constants/config';
import type { ContentFilter } from '../../features/content-studio/types';

import './AdminTheme.css';
import './AdminPanelAdvanced.css';

export default function ContentStudio() {
  // Local UI state
  const [filter, setFilter] = useState<ContentFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // React Query hooks
  const { items, isLoading, refetch } = useContentItems();
  const { publish, isPending: isPublishing } = usePublishItem();
  const { delete: deleteItem, isPending: isDeleting } = useDeleteItem();
  const { generate, isPending: isGenerating, isSuccess: isGenerateSuccess } = useGenerateDraft();
  const { translate, isPending: isTranslating } = useTranslateItem();

  // Derived data: filter and search (memoized)
  const filteredItems = useMemo(() => {
    if (filter === 'all') return items;
    return items.filter((item) => normalizeStatus(item.status) === filter);
  }, [items, filter]);

  const searchedItems = useMemo(() => {
    if (!searchQuery) return filteredItems;
    const query = searchQuery.toLowerCase();
    return filteredItems.filter(
      (item) =>
        (item.title || '').toLowerCase().includes(query) ||
        (item.type || '').toLowerCase().includes(query)
    );
  }, [filteredItems, searchQuery]);

  // Handlers
  const handlePublish = (id: string) => publish(id);

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this content?')) {
      deleteItem(id);
    }
  };

  const handleGenerateDraft = () => {
    generate({ topic: DEFAULT_TOPIC, language: DEFAULT_LANGUAGE });
  };

  const handleTranslate = (id: string) => {
    translate(id, { target_language: DEFAULT_TRANSLATION_TARGET });
  };

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
            onClick={handleGenerateDraft}
            disabled={isGenerating}
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Sparkles size={16} />
            {isGenerating ? 'Generating...' : 'AI Draft'}
          </button>
          <button
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Plus size={16} /> New Content
          </button>
          <button className="refresh-btn" onClick={() => refetch()}>
            <RefreshCw size={16} /> Refresh
          </button>
        </div>
      </div>

      {/* Stats */}
      <StatsCards items={items} isLoading={isLoading} />

      {/* Filter + Search */}
      <FilterBar
        filter={filter}
        onFilterChange={setFilter}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      {/* Content Table */}
      <ContentTable
        items={searchedItems}
        onPublish={handlePublish}
        onDelete={handleDelete}
        onTranslate={handleTranslate}
        isPublishing={isPublishing}
        isDeleting={isDeleting}
        isTranslating={isTranslating}
      />
    </div>
  );
}
