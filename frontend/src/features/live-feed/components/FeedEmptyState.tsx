/**
 * FeedEmptyState Component
 * ==========================
 * @module features/live-feed/components
 */

import { Activity } from 'lucide-react';

export function FeedEmptyState() {
  return (
    <div className="feed-empty">
      <Activity size={48} style={{ opacity: 0.3 }} />
      <p>Waiting for events...</p>
    </div>
  );
}
