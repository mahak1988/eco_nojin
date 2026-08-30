/**
 * Wallet Configuration
 * =====================
 * Initial wallet data and metadata.
 *
 * In production, this would be fetched from backend API.
 * For now, hardcoded for demo purposes.
 *
 * @module features/crypto-payment/constants
 */

import type { WalletInfo, WalletMeta, CryptoType } from '../types';

/** Initial wallets (demo data) */
export const INITIAL_WALLETS: WalletInfo[] = [
  {
    address: 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
    balance: 0.4523,
    usdValue: 28450.5,
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
    usdValue: 32450.8,
    type: 'eth',
  },
];

/** Wallet metadata for display */
export const WALLET_META: Record<CryptoType, WalletMeta> = {
  btc: {
    type: 'btc',
    name: 'Bitcoin',
    color: '#f7931a',
    i18nKey: 'crypto.btcAddress',
  },
  usdt: {
    type: 'usdt',
    name: 'Tether',
    color: '#26a17b',
    i18nKey: 'crypto.usdtAddress',
  },
  eth: {
    type: 'eth',
    name: 'Ethereum',
    color: '#627eea',
    i18nKey: 'crypto.ethAddress',
  },
};
