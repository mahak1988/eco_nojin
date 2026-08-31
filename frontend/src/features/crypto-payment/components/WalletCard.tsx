/**
 * WalletCard Component
 * =====================
 * Displays a single cryptocurrency wallet with balance and address.
 *
 * @module features/crypto-payment/components
 */

import { motion } from 'framer-motion';
import { Bitcoin, DollarSign, Copy, Check, QrCode } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { WalletInfo, CryptoType } from '../types';
import { WALLET_META } from '../constants/wallets';
import { formatUSD, formatCrypto } from '../utils/formatters';

interface WalletCardProps {
  wallet: WalletInfo;
  copiedId: string | null;
  onCopy: (text: string, id: string) => void;
}

/** Crypto icon by type */
function CryptoIcon({ type }: { type: CryptoType }) {
  if (type === 'btc') return <Bitcoin size={24} style={{ color: WALLET_META.btc.color }} />;
  if (type === 'usdt') return <DollarSign size={24} style={{ color: WALLET_META.usdt.color }} />;
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill={WALLET_META.eth.color}>
      <path d="M12 2L4 13.5l8 4.5 8-4.5L12 2zM4 15.5l8 4.5 8-4.5-8-4.5-8 4.5z" />
    </svg>
  );
}

export function WalletCard({ wallet, copiedId, onCopy }: WalletCardProps) {
  const { t } = useTranslation();
  const meta = WALLET_META[wallet.type];

  return (
    <motion.div className="glass-card" style={{ padding: '24px' }} whileHover={{ scale: 1.02 }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <CryptoIcon type={wallet.type} />
          <div>
            <div
              style={{
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--text-primary)',
              }}
            >
              {wallet.type.toUpperCase()}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{t(meta.i18nKey)}</div>
          </div>
        </div>
        <button
          className="btn-secondary"
          style={{ padding: '6px', borderRadius: '8px' }}
          aria-label="Show QR code"
        >
          <QrCode size={18} />
        </button>
      </div>

      {/* Balance */}
      <div style={{ marginBottom: '16px' }}>
        <div
          style={{
            fontSize: '11px',
            color: 'var(--text-faint)',
            marginBottom: '4px',
          }}
        >
          {t('crypto.amount')}
        </div>
        <div
          style={{
            fontSize: '24px',
            fontWeight: 800,
            color: 'var(--text-primary)',
          }}
        >
          {formatCrypto(wallet.balance)}
        </div>
        <div
          style={{
            fontSize: '13px',
            color: 'var(--accent-primary)',
            marginTop: '4px',
          }}
        >
          ≈ {formatUSD(wallet.usdValue)}
        </div>
      </div>

      {/* Address */}
      <div>
        <div
          style={{
            fontSize: '11px',
            color: 'var(--text-faint)',
            marginBottom: '4px',
          }}
        >
          Address
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 12px',
            background: 'var(--bg-hover)',
            borderRadius: '8px',
            fontFamily: 'monospace',
            fontSize: '11px',
            color: 'var(--text-secondary)',
          }}
        >
          <span
            style={{
              flex: 1,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {wallet.address}
          </span>
          <button
            onClick={() => onCopy(wallet.address, wallet.type)}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--accent-primary)',
            }}
            aria-label="Copy address"
          >
            {copiedId === wallet.type ? <Check size={14} /> : <Copy size={14} />}
          </button>
        </div>
      </div>
    </motion.div>
  );
}
