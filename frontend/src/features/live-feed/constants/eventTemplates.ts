/**
 * Event Templates & Configuration
 * =================================
 * @module features/live-feed/constants
 */

import type { EventTemplate } from '../types';

/** Default maximum number of events to display */
export const DEFAULT_MAX_ITEMS = 10;

/** Default polling interval in milliseconds */
export const DEFAULT_POLL_INTERVAL_MS = 3000;

/** Event templates for generation */
export const EVENT_TEMPLATES: EventTemplate[] = [
  {
    type: 'success',
    title: 'User Login',
    message: 'admin@econojin.com logged in',
    icon: '✓',
  },
  {
    type: 'info',
    title: 'New Order',
    message: 'Order #ORD-2026-001 created',
    icon: '🛒',
  },
  {
    type: 'warning',
    title: 'High CPU',
    message: 'CPU usage at 85%',
    icon: '⚠',
  },
  {
    type: 'success',
    title: 'Payment Received',
    message: '500,000 IRR from user_123',
    icon: '💰',
  },
  {
    type: 'info',
    title: 'Content Published',
    message: 'Article "Sustainable Farming" live',
    icon: '📄',
  },
  {
    type: 'error',
    title: 'API Error',
    message: '500 on /api/v1/ai/advise',
    icon: '✗',
  },
  {
    type: 'success',
    title: 'New User',
    message: 'farmer_456 registered',
    icon: '👤',
  },
  {
    type: 'warning',
    title: 'Low Stock',
    message: 'Organic Fertilizer: 5 left',
    icon: '📦',
  },
];

/** Event type colors */
export const EVENT_COLORS = {
  success: 'rgba(16, 185, 129, 0.15)',
  warning: 'rgba(245, 158, 11, 0.15)',
  error: 'rgba(239, 68, 68, 0.15)',
  info: 'rgba(59, 130, 246, 0.15)',
} as const;

/** Spring animation config */
export const SPRING_CONFIG = {
  type: 'spring' as const,
  stiffness: 300,
  damping: 25,
};
