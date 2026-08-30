/**
 * FeedEventItem Component
 * ==========================
 * Single event item with animation.
 *
 * @module features/live-feed/components
 */

import { memo, useMemo } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertTriangle, Info, XCircle } from 'lucide-react';
import type { FeedEvent, FeedEventType } from '../types';
import { EVENT_COLORS, SPRING_CONFIG } from '../constants/eventTemplates';

interface FeedEventItemProps {
  event: FeedEvent;
}

/**
 * Icon component for event type.
 */
function EventIcon({ type }: { type: FeedEventType }) {
  const iconProps = { size: 18 };

  switch (type) {
    case 'success':
      return <CheckCircle {...iconProps} style={{ color: 'var(--accent-primary)' }} />;
    case 'warning':
      return <AlertTriangle {...iconProps} style={{ color: 'var(--accent-secondary)' }} />;
    case 'error':
      return <XCircle {...iconProps} style={{ color: 'var(--accent-danger)' }} />;
    case 'info':
      return <Info {...iconProps} style={{ color: 'var(--accent-info)' }} />;
  }
}

/**
 * Memoized event item to prevent unnecessary re-renders.
 */
export const FeedEventItem = memo(function FeedEventItem({
  event,
}: FeedEventItemProps) {
  // Memoize timestamp formatting
  const formattedTime = useMemo(
    () =>
      event.timestamp.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
    [event.timestamp]
  );

  return (
    <motion.div
      className="live-feed-item"
      initial={{ opacity: 0, y: -20, height: 0 }}
      animate={{ opacity: 1, y: 0, height: 'auto' }}
      exit={{ opacity: 0, x: 50, height: 0 }}
      transition={SPRING_CONFIG}
      style={{ background: EVENT_COLORS[event.type] }}
      layout
    >
      <div className="feed-item-icon">
        <EventIcon type={event.type} />
      </div>
      <div className="feed-item-content">
        <div className="feed-item-title">{event.title}</div>
        <div className="feed-item-message">{event.message}</div>
      </div>
      <div className="feed-item-time">{formattedTime}</div>
    </motion.div>
  );
});
