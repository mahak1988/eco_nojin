/**
 * TransactionRow Component
 * =========================
 * Single transaction row in the transactions table.
 *
 * @module features/crypto-payment/components
 */

import { motion } from 'framer-motion';
import { Bitcoin, DollarSign } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { CryptoTransaction, CryptoType } from '../types';
import { WALLET_META } from '../constants/wallets';
import { CONFIRMED_THRESHOLD, PENDING_THRESHOLD } from '../constants/config';
import { formatUSD, formatTime, truncateAddress } from '../utils/formatters';

interface TransactionRowProps {
  tx: CryptoTransaction;
  index: number;
}

function CryptoIcon({ type }: { type: CryptoType }) {
  if (type === 'btc') return <Bitcoin size={20} style={{ color: WALLET_META.btc.color }} />;
  if (type === 'usdt') return <DollarSign size={20} style={{ color: WALLET_META.usdt.color }} />;
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill={WALLET_META.eth.color}>
      <path d="M12 2L4 13.5l8 4.5 8-4.5L12 2zM4 15.5l8 4.5 8-4.5-8-4.5-8 4.5z" />
    </svg>
  );
}

function ConfirmationIndicator({ count }: { count: number }) {
  const color =
    count >= CONFIRMED_THRESHOLD
      ? '#10b981'
      : count >= PENDING_THRESHOLD
      ? '#f59e0b'
      : '#ef4444';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
      <div
        style={{
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          background: color,
        }}
      />
      {count}/6
    </div>
  );
}

export function TransactionRow({ tx, index }: TransactionRowProps) {
  const { t } = useTranslation();

  return (
    <motion.tr
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <td>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CryptoIcon type={tx.type} />
          <span style={{ fontWeight: 600 }}>{tx.type.toUpperCase()}</span>
        </div>
      </td>
      <td style={{ fontFamily: 'monospace', fontWeight: 600 }}>
        {tx.amount.toFixed(4)}
      </td>
      <td style={{ color: 'var(--accent-primary)', fontWeight: 600 }}>
        {formatUSD(tx.usdValue)}
      </td>
      <td
        style={{
          fontFamily: 'monospace',
          fontSize: '11px',
          color: 'var(--text-muted)',
        }}
      >
        {truncateAddress(tx.from)}
      </td>
      <td>
        <ConfirmationIndicator count={tx.confirmations} />
      </td>
      <td>
        <span
          className={`status-badge ${
            tx.status === 'confirmed'
              ? 'success'
              : tx.status === 'pending'
              ? 'warning'
              : 'danger'
          }`}
        >
          {t(`crypto.${tx.status}`)}
        </span>
      </td>
      <td style={{ fontSize: '12px', color: 'var(--text-faint)' }}>
        {formatTime(tx.timestamp)}
      </td>
    </motion.tr>
  );
}
