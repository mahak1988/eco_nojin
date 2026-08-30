/**
 * Telegram Manager Types
 * =======================
 * Type definitions for Telegram bot management.
 *
 * @module features/telegram-manager/types
 */

/** Telegram bot information */
export interface TelegramBot {
  id: string;
  name: string;
  username: string;
  token: string;
  active: boolean;
  totalUsers: number;
  totalMessages: number;
  lastSeen: string;
  webhookUrl?: string;
}

/** Broadcast message */
export interface BotMessage {
  id: string;
  botId: string;
  content: string;
  sentAt: Date;
  recipientCount: number;
  status: 'sent' | 'pending' | 'failed';
}

/** Telegram statistics (derived) */
export interface TelegramStats {
  totalBots: number;
  activeBots: number;
  totalUsers: number;
  totalMessages: number;
}
