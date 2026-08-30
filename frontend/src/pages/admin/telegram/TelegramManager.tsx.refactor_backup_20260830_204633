import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Send, Bot, Users, MessageSquare, Power,
  Settings, Activity, RefreshCw, Plus, Globe,
  CheckCircle, Clock, Zap
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import '../live/LiveComponents.css';
import '../AdminTheme.css';

interface TelegramBot {
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

interface BotMessage {
  id: string;
  botId: string;
  content: string;
  sentAt: Date;
  recipientCount: number;
  status: 'sent' | 'pending' | 'failed';
}

export default function TelegramManager() {
  const { t } = useTranslation();
  const [bots, setBots] = useState<TelegramBot[]>([]);
  const [messages, setMessages] = useState<BotMessage[]>([]);
  const [selectedBot, setSelectedBot] = useState<string | null>(null);
  const [broadcastText, setBroadcastText] = useState('');
  const [loading, setLoading] = useState(true);

  // Mock data
  useEffect(() => {
    const mockBots: TelegramBot[] = [
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

    setBots(mockBots);
    setLoading(false);
  }, []);

  const toggleBot = (botId: string) => {
    setBots(prev => prev.map(b =>
      b.id === botId ? { ...b, active: !b.active } : b
    ));
  };

  const sendBroadcast = () => {
    if (!broadcastText.trim() || !selectedBot) return;

    const newMsg: BotMessage = {
      id: 'msg-' + Date.now(),
      botId: selectedBot,
      content: broadcastText,
      sentAt: new Date(),
      recipientCount: bots.find(b => b.id === selectedBot)?.totalUsers || 0,
      status: 'sent',
    };

    setMessages(prev => [newMsg, ...prev]);
    setBroadcastText('');
  };

  const totalUsers = bots.reduce((sum, b) => sum + b.totalUsers, 0);
  const totalMessages = bots.reduce((sum, b) => sum + b.totalMessages, 0);
  const activeBots = bots.filter(b => b.active).length;

  if (loading) {
    return (
      <div className="admin-page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title">
              <Send size={32} /> {t('telegram.title')}
            </h1>
            <p className="page-subtitle">{t('common.loading')}</p>
          </div>
        </div>
      </div>
    );
  }

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
          <button className="btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Plus size={16} /> New Bot
          </button>
          <button className="refresh-btn">
            <RefreshCw size={16} /> {t('common.refresh')}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid-4col">
        <motion.div className="metric-card" whileHover={{ scale: 1.02 }}>
          <div className="metric-icon" style={{ background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-info)' }}>
            <Bot size={28} />
          </div>
          <div className="metric-label">{t('telegram.totalBots')}</div>
          <div className="metric-value">{bots.length}</div>
        </motion.div>

        <motion.div className="metric-card" whileHover={{ scale: 1.02 }}>
          <div className="metric-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-primary)' }}>
            <Zap size={28} />
          </div>
          <div className="metric-label">{t('telegram.activeBots')}</div>
          <div className="metric-value" style={{ color: 'var(--accent-primary)' }}>{activeBots}</div>
        </motion.div>

        <motion.div className="metric-card" whileHover={{ scale: 1.02 }}>
          <div className="metric-icon" style={{ background: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-purple)' }}>
            <Users size={28} />
          </div>
          <div className="metric-label">{t('telegram.totalUsers')}</div>
          <div className="metric-value">{totalUsers.toLocaleString()}</div>
        </motion.div>

        <motion.div className="metric-card" whileHover={{ scale: 1.02 }}>
          <div className="metric-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-secondary)' }}>
            <MessageSquare size={28} />
          </div>
          <div className="metric-label">{t('telegram.totalMessages')}</div>
          <div className="metric-value">{totalMessages.toLocaleString()}</div>
        </motion.div>
      </div>

      {/* Bots Grid + Broadcast */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Bots List */}
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
                style={{ padding: '16px', cursor: 'pointer' }}
                whileHover={{ scale: 1.01 }}
                onClick={() => setSelectedBot(bot.id)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    <div style={{
                      width: '48px',
                      height: '48px',
                      borderRadius: '12px',
                      background: bot.active ? 'linear-gradient(135deg, #0088cc, #0066aa)' : 'var(--border-color)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: 'white',
                    }}>
                      <Send size={24} />
                    </div>
                    <div>
                      <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '15px' }}>
                        {bot.name}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--accent-info)', fontFamily: 'monospace' }}>
                        {bot.username}
                      </div>
                    </div>
                  </div>
                  <div
                    className={`toggle-switch ${bot.active ? 'active' : ''}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleBot(bot.id);
                    }}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginTop: '12px' }}>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase' }}>
                      {t('telegram.totalUsers')}
                    </div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--accent-info)' }}>
                      {bot.totalUsers.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase' }}>
                      {t('telegram.messagesSent')}
                    </div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--accent-secondary)' }}>
                      {bot.totalMessages.toLocaleString()}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '10px', color: 'var(--text-faint)', textTransform: 'uppercase' }}>
                      {t('telegram.lastSeen')}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                      {new Date(bot.lastSeen).toLocaleString()}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                  <button className="btn-secondary" style={{ flex: 1, padding: '8px', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                    <Settings size={14} /> Configure
                  </button>
                  <button className="btn-secondary" style={{ flex: 1, padding: '8px', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                    <Activity size={14} /> Logs
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* Broadcast Panel */}
        <div className="chart-container">
          <div className="chart-title">
            <Send size={20} />
            {t('telegram.sendBroadcast')}
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
              {t('telegram.targetAudience')}
            </label>
            <select
              className="form-input"
              value={selectedBot || ''}
              onChange={(e) => setSelectedBot(e.target.value)}
            >
              <option value="">-- Select Bot --</option>
              {bots.filter(b => b.active).map(b => (
                <option key={b.id} value={b.id}>
                  {b.name} ({b.username}) - {b.totalUsers.toLocaleString()} users
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
              {t('telegram.messageText')}
            </label>
            <textarea
              className="form-input"
              value={broadcastText}
              onChange={(e) => setBroadcastText(e.target.value)}
              rows={6}
              placeholder="Enter your broadcast message..."
              style={{ resize: 'vertical', fontFamily: 'inherit' }}
            />
          </div>

          <button
            className="btn-primary"
            onClick={sendBroadcast}
            disabled={!broadcastText.trim() || !selectedBot}
            style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', padding: '12px' }}
          >
            <Send size={16} />
            {t('telegram.sendBroadcast')}
          </button>

          {/* Message History */}
          <div style={{ marginTop: '24px' }}>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)', marginBottom: '12px' }}>
              Recent Broadcasts
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '300px', overflowY: 'auto' }}>
              {messages.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
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
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <CheckCircle size={14} style={{ color: 'var(--accent-primary)' }} />
                        <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-primary)' }}>
                          Sent to {msg.recipientCount.toLocaleString()} users
                        </span>
                      </div>
                      <span style={{ fontSize: '11px', color: 'var(--text-faint)' }}>
                        {msg.sentAt.toLocaleTimeString()}
                      </span>
                    </div>
                    <div style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>
                      {msg.content}
                    </div>
                  </motion.div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
