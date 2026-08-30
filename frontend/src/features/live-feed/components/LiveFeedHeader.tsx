/**
 * LiveFeedHeader Component
 * ==========================
 * @module features/live-feed/components
 */

import { Activity } from 'lucide-react';

interface LiveFeedHeaderProps {
  isPaused: boolean;
  onTogglePause: () => void;
}

export function LiveFeedHeader({
  isPaused,
  onTogglePause,
}: LiveFeedHeaderProps) {
  return (
    <div className="live-feed-header">
      <div className="live-feed-title">
        <Activity size={18} />
        Live Activity Feed
        <span className="live-indicator">●</span>
      </div>
      <button className="feed-pause-btn" onClick={onTogglePause}>
        {isPaused ? '▶ Resume' : '⏸ Pause'}
      </button>
    </div>
  );
}
