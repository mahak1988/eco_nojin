/**
 * LiveFeed Types
 * ================
 * Type definitions for live activity feed.
 *
 * @module features/live-feed/types
 */

/** Event type categories */
export type FeedEventType = 'success' | 'warning' | 'error' | 'info';

/** Single feed event */
export interface FeedEvent {
  id: string;
  type: FeedEventType;
  title: string;
  message: string;
  timestamp: Date;
  icon?: string;
}

/** Event template (for generation) */
export interface EventTemplate {
  type: FeedEventType;
  title: string;
  message: string;
  icon: string;
}

/** LiveFeed component props */
export interface LiveFeedProps {
  maxItems?: number;
  pollInterval?: number;
}
