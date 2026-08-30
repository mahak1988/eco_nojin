/**
 * TelegramManager (Orchestrator)
 * =================================
 * Telegram bot management dashboard.
 *
 * Key improvements from original (359 lines):
 * - Moved mock data from useEffect to constants (no extra render)
 * - useMemo for derived stats (totalUsers, totalMessages, activeBots)
 * - Extracted 4 components (StatsCards, BotsList, BroadcastPanel)
 * - React Query ready hooks (future API integration)
 * - 359 → ~80 lines orchestration (78% reduction)
 *
 * @module pages/admin/telegram/TelegramManager
 */

import { Send, Plus, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { useTelegramBots } from '../../../features/telegram-manager/hooks/useTelegramBots';
import { useBroadcastMessage } from '../../../features/telegram-manager/hooks/useBroadcastMessage';
import { useTelegramStats } from '../../../features/telegram-manager/hooks/useTelegramStats';
import { StatsCards } from '../../../features/telegram-manager/components/StatsCards';
import { BotsList } from '../../../features/telegram-manager/components/BotsList';
import { BroadcastPanel } from '../../../features/telegram-manager/components/BroadcastPanel';

import '../live/LiveComponents.css';
import '../AdminTheme.css';

export default function TelegramManager() {
  const { t } = useTranslation();

  // Hooks
  const { bots, toggleBot } = useTelegramBots();
  const stats = useTelegramStats(bots);
  const {
    messages,
    broadcastText,
    selectedBot,
    setBroadcastText,
    setSelectedBot,
    sendBroadcast,
    canSend,
  } = useBroadcastMessage();

  const handleSendBroadcast = () => {
    sendBroadcast(bots);
  };

  return (
    <div className="admin-page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Send size={32} style={{ color: 'var(--accent-info)' }} />
            {t('telegram.title')}
          </h1>
          <p className="page-subtitle">{t('telegram.subtitle')}</p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Plus size={16} /> New Bot
          </button>
          <button className="refresh-btn">
            <RefreshCw size={16} /> {t('common.refresh')}
          </button>
        </div>
      </div>

      {/* Stats */}
      <StatsCards stats={stats} />

      {/* Bots Grid + Broadcast */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <BotsList
          bots={bots}
          selectedBot={selectedBot}
          onSelectBot={setSelectedBot}
          onToggleBot={toggleBot}
        />
        <BroadcastPanel
          bots={bots}
          messages={messages}
          selectedBot={selectedBot}
          broadcastText={broadcastText}
          canSend={canSend}
          onSelectBot={setSelectedBot}
          onBroadcastTextChange={setBroadcastText}
          onSendBroadcast={handleSendBroadcast}
        />
      </div>
    </div>
  );
}
