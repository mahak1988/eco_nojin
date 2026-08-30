import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Wallet, Bitcoin, DollarSign, Copy, Check,
  RefreshCw, ArrowUpRight, QrCode, ExternalLink
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import '../live/LiveComponents.css';
import '../AdminTheme.css';

interface CryptoTransaction {
  id: string;
  type: 'btc' | 'usdt' | 'eth';
  amount: number;
  usdValue: number;
  from: string;
  status: 'confirmed' | 'pending' | 'failed';
  confirmations: number;
  timestamp: Date;
  txHash: string;
}

interface WalletInfo {
  address: string;
  balance: number;
  usdValue: number;
  type: 'btc' | 'usdt' | 'eth';
}

export default function CryptoPaymentWidget() {
  const { t } = useTranslation();
  const [wallets, setWallets] = useState<WalletInfo[]>([]);
  const [transactions, setTransactions] = useState<CryptoTransaction[]>([]);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  // Simulated wallet data (in real app, fetch from backend)
  useEffect(() => {
    const initialWallets: WalletInfo[] = [
      {
        address: 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
        balance: 0.4523,
        usdValue: 28450.50,
        type: 'btc',
      },
      {
        address: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
        balance: 15420.75,
        usdValue: 15420.75,
        type: 'usdt',
      },
      {
        address: '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb',
        balance: 12.847,
        usdValue: 32450.80,
        type: 'eth',
      },
    ];

    setWallets(initialWallets);

    // Simulate live transactions
    const interval = setInterval(() => {
      const newTx: CryptoTransaction = {
        id: 'tx-' + Date.now(),
        type: ['btc', 'usdt', 'eth'][Math.floor(Math.random() * 3)] as any,
        amount: Math.random() * 1000,
        usdValue: Math.random() * 10000,
        from: '0x' + Math.random().toString(16).substr(2, 16),
        status: Math.random() > 0.3 ? 'confirmed' : Math.random() > 0.5 ? 'pending' : 'failed',
        confirmations: Math.floor(Math.random() * 10),
        timestamp: new Date(),
        txHash: '0x' + Math.random().toString(16).substr(2, 64),
      };

      setTransactions(prev => [newTx, ...prev].slice(0, 10));
      setLastUpdate(new Date());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const iconMap = {
    btc: <Bitcoin size={24} style={{ color: '#f7931a' }} />,
    usdt: <DollarSign size={24} style={{ color: '#26a17b' }} />,
    eth: <svg width="24" height="24" viewBox="0 0 24 24" fill="#627eea"><path d="M12 2L4 13.5l8 4.5 8-4.5L12 2zM4 15.5l8 4.5 8-4.5-8-4.5-8 4.5z"/></svg>,
  };

  const typeLabels = {
    btc: t('crypto.btcAddress'),
    usdt: t('crypto.usdtAddress'),
    eth: t('crypto.ethAddress'),
  };

  const totalUsdValue = wallets.reduce((sum, w) => sum + w.usdValue, 0);
  const pendingCount = transactions.filter(tx => tx.status === 'pending').length;

  return (
    <div className="admin-page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Wallet size={32} style={{ color: 'var(--accent-primary)' }} />
            {t('crypto.title')}
          </h1>
          <p className="page-subtitle">{t('crypto.subtitle')}</p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div className="live-indicator">
            <span className="live-dot" />
            {t('common.live')}
          </div>
          <button className="refresh-btn" onClick={() => setLastUpdate(new Date())}>
            <RefreshCw size={16} /> {t('common.refresh')}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid-3col">
        <motion.div
          className="metric-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <div className="metric-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-primary)' }}>
            <Wallet size={28} />
          </div>
          <div className="metric-label">{t('crypto.walletBalance')}</div>
          <div className="metric-value" style={{ fontSize: '24px' }}>
            ${totalUsdValue.toLocaleString('en-US', { maximumFractionDigits: 2 })}
          </div>
        </motion.div>

        <motion.div
          className="metric-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <div className="metric-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-secondary)' }}>
            <ArrowUpRight size={28} />
          </div>
          <div className="metric-label">{t('crypto.pendingTx')}</div>
          <div className="metric-value" style={{ color: 'var(--accent-secondary)' }}>
            {pendingCount}
          </div>
        </motion.div>

        <motion.div
          className="metric-card"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <div className="metric-icon" style={{ background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-info)' }}>
            <ArrowUpRight size={28} />
          </div>
          <div className="metric-label">{t('crypto.totalReceived')}</div>
          <div className="metric-value" style={{ fontSize: '24px' }}>
            ${totalUsdValue.toLocaleString('en-US', { maximumFractionDigits: 2 })}
          </div>
        </motion.div>
      </div>

      {/* Wallets Grid */}
      <div className="grid-3col" style={{ marginBottom: '24px' }}>
        {wallets.map((wallet) => (
          <motion.div
            key={wallet.type}
            className="glass-card"
            style={{ padding: '24px' }}
            whileHover={{ scale: 1.02 }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                {iconMap[wallet.type]}
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {wallet.type.toUpperCase()}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {typeLabels[wallet.type]}
                  </div>
                </div>
              </div>
              <button
                className="btn-secondary"
                style={{ padding: '6px', borderRadius: '8px' }}
                onClick={() => {/* Show QR code */}}
              >
                <QrCode size={18} />
              </button>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-faint)', marginBottom: '4px' }}>
                {t('crypto.amount')}
              </div>
              <div style={{ fontSize: '24px', fontWeight: 800, color: 'var(--text-primary)' }}>
                {wallet.balance.toLocaleString('en-US', { maximumFractionDigits: 4 })}
              </div>
              <div style={{ fontSize: '13px', color: 'var(--accent-primary)', marginTop: '4px' }}>
                ≈ ${wallet.usdValue.toLocaleString('en-US', { maximumFractionDigits: 2 })}
              </div>
            </div>

            <div>
              <div style={{ fontSize: '11px', color: 'var(--text-faint)', marginBottom: '4px' }}>
                Address
              </div>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px 12px',
                background: 'var(--bg-hover)',
                borderRadius: '8px',
                fontFamily: 'monospace',
                fontSize: '11px',
                color: 'var(--text-secondary)',
              }}>
                <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {wallet.address}
                </span>
                <button
                  onClick={() => copyToClipboard(wallet.address, wallet.type)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent-primary)' }}
                >
                  {copiedId === wallet.type ? <Check size={14} /> : <Copy size={14} />}
                </button>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Recent Transactions */}
      <div className="chart-container">
        <div className="chart-title">
          <ArrowUpRight size={20} />
          {t('crypto.recentTransactions')}
        </div>

        <table className="admin-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>{t('crypto.amount')}</th>
              <th>USD Value</th>
              <th>From</th>
              <th>{t('crypto.confirmations')}</th>
              <th>{t('crypto.status')}</th>
              <th>Time</th>
            </tr>
          </thead>
          <tbody>
            {transactions.map((tx, i) => (
              <motion.tr
                key={tx.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {iconMap[tx.type]}
                    <span style={{ fontWeight: 600 }}>{tx.type.toUpperCase()}</span>
                  </div>
                </td>
                <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                  {tx.amount.toFixed(4)}
                </td>
                <td style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>
                  ${tx.usdValue.toFixed(2)}
                </td>
                <td style={{ fontFamily: 'monospace', fontSize: '11px', color: 'var(--text-muted)' }}>
                  {tx.from}...
                </td>
                <td>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: tx.confirmations >= 6 ? '#10b981' : tx.confirmations >= 3 ? '#f59e0b' : '#ef4444',
                    }} />
                    {tx.confirmations}/6
                  </div>
                </td>
                <td>
                  <span className={`status-badge ${
                    tx.status === 'confirmed' ? 'success' :
                    tx.status === 'pending' ? 'warning' : 'danger'
                  }`}>
                    {t(`crypto.${tx.status}`)}
                  </span>
                </td>
                <td style={{ fontSize: '12px', color: 'var(--text-faint)' }}>
                  {tx.timestamp.toLocaleTimeString()}
                </td>
              </motion.tr>
            ))}
            {transactions.length === 0 && (
              <tr>
                <td colSpan={7} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  {t('common.loading')}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
