/**
 * useBroadcastMessage Hook
 * =========================
 * Manages broadcast message state and sending.
 *
 * @module features/telegram-manager/hooks
 */

import { useState, useCallback } from 'react';
import type { BotMessage, TelegramBot } from '../types';

interface UseBroadcastMessageReturn {
  messages: BotMessage[];
  broadcastText: string;
  selectedBot: string | null;
  setBroadcastText: (text: string) => void;
  setSelectedBot: (botId: string | null) => void;
  sendBroadcast: (bots: TelegramBot[]) => void;
  canSend: boolean;
}

export function useBroadcastMessage(): UseBroadcastMessageReturn {
  const [messages, setMessages] = useState<BotMessage[]>([]);
  const [broadcastText, setBroadcastText] = useState('');
  const [selectedBot, setSelectedBot] = useState<string | null>(null);

  const canSend = broadcastText.trim().length > 0 && selectedBot !== null;

  const sendBroadcast = useCallback(
    (bots: TelegramBot[]) => {
      if (!canSend || !selectedBot) return;

      const bot = bots.find((b) => b.id === selectedBot);
      if (!bot) return;

      const newMsg: BotMessage = {
        id: `msg-${Date.now()}`,
        botId: selectedBot,
        content: broadcastText,
        sentAt: new Date(),
        recipientCount: bot.totalUsers,
        status: 'sent',
      };

      setMessages((prev) => [newMsg, ...prev]);
      setBroadcastText('');
    },
    [broadcastText, selectedBot, canSend]
  );

  return {
    messages,
    broadcastText,
    selectedBot,
    setBroadcastText,
    setSelectedBot,
    sendBroadcast,
    canSend,
  };
}
