/**
 * BroadcastPanel Component
 * ==========================
 * @module features/telegram-manager/components
 */

import { motion } from 'framer-motion';
import { Send, CheckCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { TelegramBot, BotMessage } from '../types';
import { formatNumber, formatTime } from '../utils/formatters';

interface BroadcastPanelProps {
  bots: TelegramBot[];
  messages: BotMessage[];
  selectedBot: string | null;
  broadcastText: string;
  canSend: boolean;
  onSelectBot: (botId: string | null) => void;
  onBroadcastTextChange: (text: string) => void;
  onSendBroadcast: () => void;
}

export function BroadcastPanel({
  bots,
  messages,
  selectedBot,
  broadcastText,
  canSend,
  onSelectBot,
  onBroadcastTextChange,
  onSendBroadcast,
}: BroadcastPanelProps) {
  const { t } = useTranslation();
  const activeBots = bots.filter((b) => b.active);

  return (
    <div className="chart-container">
      <div className="chart-title">
        <Send size={20} />
        {t('telegram.sendBroadcast')}
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label
          style={{
            display: 'block',
            fontSize: '12px',
            color: 'var(--text-muted)',
            marginBottom: '8px',
          }}
        >
          {t('telegram.targetAudience')}
        </label>
        <select
          className="form-input"
          value={selectedBot || ''}
          onChange={(e) => onSelectBot(e.target.value || null)}
        >
          <option value="">-- Select Bot --</option>
          {activeBots.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name} ({b.username}) - {formatNumber(b.totalUsers)} users
            </option>
          ))}
        </select>
      </div>

      <div style={{ marginBottom: '16px' }}>
        <label
          style={{
            display: 'block',
            fontSize: '12px',
            color: 'var(--text-muted)',
            marginBottom: '8px',
          }}
        >
          {t('telegram.messageText')}
        </label>
        <textarea
          className="form-input"
          value={broadcastText}
          onChange={(e) => onBroadcastTextChange(e.target.value)}
          rows={6}
          placeholder="Enter your broadcast message..."
          style={{ resize: 'vertical', fontFamily: 'inherit' }}
        />
      </div>

      <button
        className="btn-primary"
        onClick={onSendBroadcast}
        disabled={!canSend}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          padding: '12px',
        }}
      >
        <Send size={16} />
        {t('telegram.sendBroadcast')}
      </button>

      {/* Message History */}
      <div style={{ marginTop: '24px' }}>
        <div
          style={{
            fontSize: '13px',
            fontWeight: 600,
            color: 'var(--text-primary)',
            marginBottom: '12px',
          }}
        >
          Recent Broadcasts
        </div>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
            maxHeight: '300px',
            overflowY: 'auto',
          }}
        >
          {messages.length === 0 ? (
            <div
              style={{
                textAlign: 'center',
                padding: '32px',
                color: 'var(--text-muted)',
              }}
            >
              {t('common.noData')}
            </div>
          ) : (
            messages.map((msg) => (
              <motion.div
                key={msg.id}
                className="glass-card"
                style={{ padding: '12px' }}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px',
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '8px',
                    }}
                  >
                    <CheckCircle size={14} style={{ color: 'var(--accent-primary)' }} />
                    <span
                      style={{
                        fontSize: '12px',
                        fontWeight: 600,
                        color: 'var(--text-primary)',
                      }}
                    >
                      Sent to {formatNumber(msg.recipientCount)} users
                    </span>
                  </div>
                  <span style={{ fontSize: '11px', color: 'var(--text-faint)' }}>
                    {formatTime(msg.sentAt)}
                  </span>
                </div>
                <div
                  style={{
                    fontSize: '13px',
                    color: 'var(--text-secondary)',
                    lineHeight: '1.5',
                  }}
                >
                  {msg.content}
                </div>
              </motion.div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
