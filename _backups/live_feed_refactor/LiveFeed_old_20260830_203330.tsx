import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, CheckCircle, AlertTriangle, Info, XCircle } from 'lucide-react';
import './LiveComponents.css';

interface FeedEvent {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  icon?: string;
}

interface LiveFeedProps {
  maxItems?: number;
  pollInterval?: number;
}

export default function LiveFeed({ maxItems = 10, pollInterval = 3000 }: LiveFeedProps) {
  const [events, setEvents] = useState<FeedEvent[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const intervalRef = useRef<number | null>(null);

  const eventTypes = [
    { type: 'success', title: 'User Login', message: 'admin@econojin.com logged in', icon: '✓' },
    { type: 'info', title: 'New Order', message: 'Order #ORD-2026-001 created', icon: '🛒' },
    { type: 'warning', title: 'High CPU', message: 'CPU usage at 85%', icon: '⚠' },
    { type: 'success', title: 'Payment Received', message: '500,000 IRR from user_123', icon: '💰' },
    { type: 'info', title: 'Content Published', message: 'Article "Sustainable Farming" live', icon: '📄' },
    { type: 'error', title: 'API Error', message: '500 on /api/v1/ai/advise', icon: '✗' },
    { type: 'success', title: 'New User', message: 'farmer_456 registered', icon: '👤' },
    { type: 'warning', title: 'Low Stock', message: 'Organic Fertilizer: 5 left', icon: '📦' },
  ];

  const addEvent = () => {
    const template = eventTypes[Math.floor(Math.random() * eventTypes.length)];
    const newEvent: FeedEvent = {
      id: 'evt-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9),
      type: template.type as any,
      title: template.title,
      message: template.message,
      timestamp: new Date(),
    };

    setEvents(prev => [newEvent, ...prev].slice(0, maxItems));
  };

  useEffect(() => {
    if (!isPaused) {
      addEvent();
      intervalRef.current = window.setInterval(addEvent, pollInterval);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPaused, pollInterval]);

  const iconMap = {
    success: <CheckCircle size={18} style={{ color: 'var(--accent-primary)' }} />,
    warning: <AlertTriangle size={18} style={{ color: 'var(--accent-secondary)' }} />,
    error: <XCircle size={18} style={{ color: 'var(--accent-danger)' }} />,
    info: <Info size={18} style={{ color: 'var(--accent-info)' }} />,
  };

  const colorMap = {
    success: 'rgba(16, 185, 129, 0.15)',
    warning: 'rgba(245, 158, 11, 0.15)',
    error: 'rgba(239, 68, 68, 0.15)',
    info: 'rgba(59, 130, 246, 0.15)',
  };

  return (
    <div className="live-feed-container">
      <div className="live-feed-header">
        <div className="live-feed-title">
          <Activity size={18} />
          Live Activity Feed
          <span className="live-indicator">●</span>
        </div>
        <button
          className="feed-pause-btn"
          onClick={() => setIsPaused(!isPaused)}
        >
          {isPaused ? '▶ Resume' : '⏸ Pause'}
        </button>
      </div>

      <div className="live-feed-list">
        <AnimatePresence initial={false}>
          {events.map((event) => (
            <motion.div
              key={event.id}
              className="live-feed-item"
              initial={{ opacity: 0, y: -20, height: 0 }}
              animate={{ opacity: 1, y: 0, height: 'auto' }}
              exit={{ opacity: 0, x: 50, height: 0 }}
              transition={{ type: 'spring', stiffness: 300, damping: 25 }}
              style={{ background: colorMap[event.type] }}
              layout
            >
              <div className="feed-item-icon">
                {iconMap[event.type]}
              </div>
              <div className="feed-item-content">
                <div className="feed-item-title">{event.title}</div>
                <div className="feed-item-message">{event.message}</div>
              </div>
              <div className="feed-item-time">
                {event.timestamp.toLocaleTimeString('en-US', { 
                  hour: '2-digit', 
                  minute: '2-digit',
                  second: '2-digit'
                })}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {events.length === 0 && (
          <div className="feed-empty">
            <Activity size={48} style={{ opacity: 0.3 }} />
            <p>Waiting for events...</p>
          </div>
        )}
      </div>
    </div>
  );
}
