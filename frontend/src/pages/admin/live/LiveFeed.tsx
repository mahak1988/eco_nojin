/**
 * LiveFeed (Orchestrator)
 * =========================
 * Live activity feed component.
 *
 * Key improvements from original (145 lines):
 * - Fixed stale closure bug (ref-based interval pattern)
 * - Deterministic event generation (seed-based, no Math.random)
 * - Removed 'as any' type assertion
 * - Replaced deprecated 'substr' with 'slice'
 * - Memoized event items for performance
 * - Extracted 3 reusable components
 * - 145 → ~60 lines (59% reduction)
 *
 * @module pages/admin/live/LiveFeed
 */

import { AnimatePresence } from 'framer-motion';

import { useLiveFeedEvents } from '../../../features/live-feed/hooks/useLiveFeedEvents';
import { LiveFeedHeader } from '../../../features/live-feed/components/LiveFeedHeader';
import { FeedEventItem } from '../../../features/live-feed/components/FeedEventItem';
import { FeedEmptyState } from '../../../features/live-feed/components/FeedEmptyState';

import './LiveComponents.css';

interface LiveFeedProps {
  maxItems?: number;
  pollInterval?: number;
}

export default function LiveFeed({ maxItems = 10, pollInterval = 3000 }: LiveFeedProps) {
  // Custom hook manages all state and interval logic
  const { events, isPaused, togglePause } = useLiveFeedEvents({
    maxItems,
    pollInterval,
    autoStart: true,
  });

  return (
    <div className="live-feed-container">
      <LiveFeedHeader isPaused={isPaused} onTogglePause={togglePause} />

      <div className="live-feed-list">
        <AnimatePresence initial={false}>
          {events.map((event) => (
            <FeedEventItem key={event.id} event={event} />
          ))}
        </AnimatePresence>

        {events.length === 0 && <FeedEmptyState />}
      </div>
    </div>
  );
}
