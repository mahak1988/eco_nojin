/**
 * BotsList Component
 * ===================
 * @module features/telegram-manager/components
 */

import { motion } from 'framer-motion';
import { Send, Bot, Settings, Activity } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { TelegramBot } from '../types';
import { formatNumber, formatDateTime } from '../utils/formatters';

interface BotsListProps {
  bots: TelegramBot[];
  selectedBot: string | null;
  onSelectBot: (botId: string) => void;
  onToggleBot: (botId: string) => void;
}

export function BotsList({
  bots,
  selectedBot,
  onSelectBot,
  onToggleBot,
}: BotsListProps) {
  const { t } = useTranslation();

  return (
    <div className="chart-container">
      <div className="chart-title">
        <Bot size={20} />
        {t('telegram.title')}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {bots.map((bot) => (
          <motion.div
            key={bot.id}
            className="glass-card"
            style={{
              padding: '16px',
              cursor: 'pointer',
              border:
                selectedBot === bot.id
                  ? '2px solid var(--accent-info)'
                  : '2px solid transparent',
            }}
            whileHover={{ scale: 1.01 }}
            onClick={() => onSelectBot(bot.id)}
          >
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                marginBottom: '12px',
              }}
            >
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                <div
                  style={{
                    width: '48px',
                    height: '48px',
                    borderRadius: '12px',
                    background: bot.active
                      ? 'linear-gradient(135deg, #0088cc, #0066aa)'
                      : 'var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                  }}
                >
                  <Send size={24} />
                </div>
                <div>
                  <div
                    style={{
                      fontWeight: 700,
                      color: 'var(--text-primary)',
                      fontSize: '15px',
                    }}
                  >
                    {bot.name}
                  </div>
                  <div
                    style={{
                      fontSize: '12px',
                      color: 'var(--accent-info)',
                      fontFamily: 'monospace',
                    }}
                  >
                    {bot.username}
                  </div>
                </div>
              </div>
              <div
                className={`toggle-switch ${bot.active ? 'active' : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  onToggleBot(bot.id);
                }}
              />
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr 1fr',
                gap: '12px',
                marginTop: '12px',
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: '10px',
                    color: 'var(--text-faint)',
                    textTransform: 'uppercase',
                  }}
                >
                  {t('telegram.totalUsers')}
                </div>
                <div
                  style={{
                    fontSize: '16px',
                    fontWeight: 700,
                    color: 'var(--accent-info)',
                  }}
                >
                  {formatNumber(bot.totalUsers)}
                </div>
              </div>
              <div>
                <div
                  style={{
                    fontSize: '10px',
                    color: 'var(--text-faint)',
                    textTransform: 'uppercase',
                  }}
                >
                  {t('telegram.messagesSent')}
                </div>
                <div
                  style={{
                    fontSize: '16px',
                    fontWeight: 700,
                    color: 'var(--accent-secondary)',
                  }}
                >
                  {formatNumber(bot.totalMessages)}
                </div>
              </div>
              <div>
                <div
                  style={{
                    fontSize: '10px',
                    color: 'var(--text-faint)',
                    textTransform: 'uppercase',
                  }}
                >
                  {t('telegram.lastSeen')}
                </div>
                <div
                  style={{
                    fontSize: '12px',
                    color: 'var(--text-secondary)',
                  }}
                >
                  {formatDateTime(bot.lastSeen)}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
              <button
                className="btn-secondary"
                style={{
                  flex: 1,
                  padding: '8px',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <Settings size={14} /> Configure
              </button>
              <button
                className="btn-secondary"
                style={{
                  flex: 1,
                  padding: '8px',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px',
                }}
              >
                <Activity size={14} /> Logs
              </button>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
