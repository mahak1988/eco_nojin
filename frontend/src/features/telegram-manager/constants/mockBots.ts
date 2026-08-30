/**
 * Mock Bots Data
 * ===============
 * Initial mock data for Telegram bots.
 *
 * This replaces the useEffect-based mock data initialization.
 * In production, this would be fetched from API via React Query.
 *
 * @module features/telegram-manager/constants
 */

import type { TelegramBot } from '../types';

/** Mock Telegram bots */
export const MOCK_BOTS: TelegramBot[] = [
  {
    id: 'bot-1',
    name: 'Eco Nojin Main',
    username: '@econojin_bot',
    token: '***',
    active: true,
    totalUsers: 15420,
    totalMessages: 89543,
    lastSeen: new Date().toISOString(),
    webhookUrl: 'https://api.econojin.com/webhook/telegram',
  },
  {
    id: 'bot-2',
    name: 'Marketplace Bot',
    username: '@econojin_market_bot',
    token: '***',
    active: true,
    totalUsers: 8234,
    totalMessages: 45678,
    lastSeen: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: 'bot-3',
    name: 'Support Bot',
    username: '@econojin_support_bot',
    token: '***',
    active: false,
    totalUsers: 2341,
    totalMessages: 12456,
    lastSeen: new Date(Date.now() - 86400000).toISOString(),
  },
];
