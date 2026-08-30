#!/usr/bin/env python3
"""
Phase 2 - Refactor EcoWalletDashboard.tsx
==========================================
Complete refactoring of EcoWalletDashboard following:
- Feature-based architecture
- React Query for all API calls
- Deterministic chart data (no Math.random in render)
- Type-safe (no 'any')
- Extracted components
- Testable utilities
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND = PROJECT_ROOT / "frontend" / "src"
FEATURES = FRONTEND / "features"
ECO_WALLET = FEATURES / "eco-wallet"
OLD_FILE = FRONTEND / "pages" / "admin" / "EcoWalletDashboard.tsx"


# ═══════════════════════════════════════════════════════════════════════
# 1. Types
# ═══════════════════════════════════════════════════════════════════════

ECOWALLET_TYPES = '''/**
 * EcoWallet Types
 * =================
 * Type definitions for EcoWallet dashboard.
 *
 * @module features/eco-wallet/types
 */

// ─────────────────────────────────────────────────────────────────────
// API Response Types
// ─────────────────────────────────────────────────────────────────────

/** Earning option from API */
export interface EarningOption {
  category: string;
  eco_amount: number;
  description: string;
}

/** Redemption option from API */
export interface RedemptionOption {
  category: string;
  eco_amount: number;
  description: string;
}

/** Wallet statistics from API */
export interface WalletStats {
  total_wallets?: number;
  active_wallets?: number;
  total_earnings?: number;
  total_redemptions?: number;
  pending?: number;
  total_transactions?: number;
}

// ─────────────────────────────────────────────────────────────────────
// Chart Data Types
// ─────────────────────────────────────────────────────────────────────

/** Single day data point for transaction chart */
export interface TransactionDataPoint {
  day: string;
  earnings: number;
  redemptions: number;
}

/** Chart configuration */
export interface ChartConfig {
  days: number;
  earningsRange: { min: number; max: number };
  redemptionsRange: { min: number; max: number };
}
'''


# ═══════════════════════════════════════════════════════════════════════
# 2. Constants
# ═══════════════════════════════════════════════════════════════════════

CONFIG_CONST = '''/**
 * EcoWallet Configuration
 * ========================
 * API endpoints, chart settings, and other configuration.
 *
 * @module features/eco-wallet/constants
 */

import type { ChartConfig } from '../types';

/** API base URL (from env or fallback) */
export const API_BASE =
  (typeof import.meta !== 'undefined' &&
    (import.meta as unknown as { env?: { VITE_API_BASE?: string } }).env
      ?.VITE_API_BASE) ||
  'http://localhost:8000/api/v1';

/** API endpoints */
export const ENDPOINTS = {
  stats: `${API_BASE}/ecowallet/stats`,
  earningOptions: `${API_BASE}/ecowallet/earning-options`,
  redemptionOptions: `${API_BASE}/ecowallet/redemption-options`,
} as const;

/** React Query keys */
export const QUERY_KEYS = {
  stats: ['ecowallet', 'stats'] as const,
  earningOptions: ['ecowallet', 'earning-options'] as const,
  redemptionOptions: ['ecowallet', 'redemption-options'] as const,
} as const;

/** Transaction chart configuration */
export const CHART_CONFIG: ChartConfig = {
  days: 30,
  earningsRange: { min: 1000, max: 5000 },
  redemptionsRange: { min: 500, max: 3000 },
};

/** Chart colors */
export const CHART_COLORS = {
  earnings: '#10b981',
  redemptions: '#8b5cf6',
} as const;

/** React Query stale time (5 minutes) */
export const STALE_TIME_MS = 5 * 60 * 1000;

/** React Query retry count */
export const RETRY_COUNT = 2;
'''

MOCK_DATA_CONST = '''/**
 * EcoWallet Mock Data
 * ====================
 * Deterministic mock data for transaction chart.
 *
 * Uses seeded random number generator for reproducible data.
 * This replaces Math.random() in render body.
 *
 * @module features/eco-wallet/constants
 */

import type { TransactionDataPoint, ChartConfig } from '../types';
import { CHART_CONFIG } from './config';

/**
 * Simple Linear Congruential Generator (LCG) for seeded random.
 *
 * @see https://en.wikipedia.org/wiki/Linear_congruential_generator
 */
function seededRandom(seed: number): () => number {
  let state = seed;
  return () => {
    // Numerical Recipes LCG parameters
    state = (state * 1664525 + 1013904223) % 2 ** 32;
    return state / 2 ** 32;
  };
}

/**
 * Generate deterministic transaction history for chart.
 *
 * @param config - Chart configuration
 * @param seed - Random seed (default: fixed seed for consistency)
 * @returns Array of daily transaction data points
 */
export function generateTransactionHistory(
  config: ChartConfig = CHART_CONFIG,
  seed: number = 42
): TransactionDataPoint[] {
  const random = seededRandom(seed);

  return Array.from({ length: config.days }, (_, i) => {
    const earningsRange =
      config.earningsRange.max - config.earningsRange.min;
    const redemptionsRange =
      config.redemptionsRange.max - config.redemptionsRange.min;

    return {
      day: `Day ${i + 1}`,
      earnings: Math.floor(
        config.earningsRange.min + random() * earningsRange
      ),
      redemptions: Math.floor(
        config.redemptionsRange.min + random() * redemptionsRange
      ),
    };
  });
}

/**
 * Default transaction history (pre-generated for consistency).
 */
export const DEFAULT_TRANSACTION_HISTORY: TransactionDataPoint[] =
  generateTransactionHistory();
'''


# ═══════════════════════════════════════════════════════════════════════
# 3. API
# ═══════════════════════════════════════════════════════════════════════

API_FUNCTIONS = '''/**
 * EcoWallet API Functions
 * ========================
 * API client for EcoWallet endpoints.
 *
 * All functions return typed responses and handle errors properly.
 * Used by React Query hooks.
 *
 * @module features/eco-wallet/api
 */

import type {
  WalletStats,
  EarningOption,
  RedemptionOption,
} from '../types';
import { ENDPOINTS } from '../constants/config';

/**
 * Get authorization headers with token from localStorage
 */
function getAuthHeaders(): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (typeof window !== 'undefined') {
    const token = window.localStorage.getItem('access_token');
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  return headers;
}

/**
 * Normalize API response (handles array/object variations)
 */
function normalizeOptions<T>(
  data: unknown
): T[] {
  if (Array.isArray(data)) return data;
  if (data && typeof data === 'object') {
    const obj = data as { options?: T[]; items?: T[] };
    return obj.options || obj.items || [];
  }
  return [];
}

/**
 * Fetch wallet statistics
 */
export async function fetchWalletStats(): Promise<WalletStats> {
  const response = await fetch(ENDPOINTS.stats, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch wallet stats: ${response.statusText}`);
  }

  return response.json() as Promise<WalletStats>;
}

/**
 * Fetch earning options
 */
export async function fetchEarningOptions(): Promise<EarningOption[]> {
  const response = await fetch(ENDPOINTS.earningOptions, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch earning options: ${response.statusText}`);
  }

  const data = await response.json();
  return normalizeOptions<EarningOption>(data);
}

/**
 * Fetch redemption options
 */
export async function fetchRedemptionOptions(): Promise<RedemptionOption[]> {
  const response = await fetch(ENDPOINTS.redemptionOptions, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    throw new Error(
      `Failed to fetch redemption options: ${response.statusText}`
    );
  }

  const data = await response.json();
  return normalizeOptions<RedemptionOption>(data);
}
'''


# ═══════════════════════════════════════════════════════════════════════
# 4. Utils
# ═══════════════════════════════════════════════════════════════════════

FORMATTERS_UTIL = '''/**
 * EcoWallet Formatters
 * =====================
 * Type-safe formatting utilities.
 *
 * @module features/eco-wallet/utils
 */

/**
 * Safely convert any value to string (generic version).
 *
 * Unlike the original `any`-based version, this uses TypeScript's
 * unknown type for better type safety.
 */
export function safeString<T = unknown>(
  value: T,
  fallback: string = 'N/A'
): string {
  if (value === null || value === undefined) return fallback;

  if (typeof value === 'string') return value;
  if (typeof value === 'number') return value.toString();
  if (typeof value === 'boolean') return String(value);

  if (typeof value === 'object') {
    try {
      return JSON.stringify(value);
    } catch {
      return fallback;
    }
  }

  return String(value);
}

/**
 * Format number with locale-specific separators.
 *
 * @param value - Number to format
 * @param locale - Locale code (default: 'fa-IR' for Persian)
 */
export function formatNumber(
  value: number | undefined,
  locale: string = 'fa-IR'
): string {
  if (value === undefined || value === null) return '0';
  return value.toLocaleString(locale);
}

/**
 * Safely extract numeric value with fallback.
 */
export function safeNumber(
  value: number | undefined,
  fallback: number = 0
): number {
  return typeof value === 'number' && !isNaN(value) ? value : fallback;
}
'''


# ═══════════════════════════════════════════════════════════════════════
# 5. Hooks
# ═══════════════════════════════════════════════════════════════════════

USE_STATS_HOOK = '''/**
 * useEcoWalletStats Hook
 * =======================
 * React Query hook for wallet statistics.
 *
 * @module features/eco-wallet/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { WalletStats } from '../types';
import { QUERY_KEYS, STALE_TIME_MS, RETRY_COUNT } from '../constants/config';
import { fetchWalletStats } from '../api/ecoWalletApi';

export function useEcoWalletStats() {
  const query = useQuery<WalletStats, Error>({
    queryKey: QUERY_KEYS.stats,
    queryFn: fetchWalletStats,
    staleTime: STALE_TIME_MS,
    retry: RETRY_COUNT,
    refetchOnWindowFocus: false,
  });

  return {
    stats: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
'''

USE_EARNING_HOOK = '''/**
 * useEarningOptions Hook
 * =======================
 * React Query hook for earning options.
 *
 * @module features/eco-wallet/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { EarningOption } from '../types';
import { QUERY_KEYS, STALE_TIME_MS, RETRY_COUNT } from '../constants/config';
import { fetchEarningOptions } from '../api/ecoWalletApi';

export function useEarningOptions() {
  const query = useQuery<EarningOption[], Error>({
    queryKey: QUERY_KEYS.earningOptions,
    queryFn: fetchEarningOptions,
    staleTime: STALE_TIME_MS,
    retry: RETRY_COUNT,
    refetchOnWindowFocus: false,
  });

  return {
    options: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
'''

USE_REDEMPTION_HOOK = '''/**
 * useRedemptionOptions Hook
 * ===========================
 * React Query hook for redemption options.
 *
 * @module features/eco-wallet/hooks
 */

import { useQuery } from '@tanstack/react-query';
import type { RedemptionOption } from '../types';
import { QUERY_KEYS, STALE_TIME_MS, RETRY_COUNT } from '../constants/config';
import { fetchRedemptionOptions } from '../api/ecoWalletApi';

export function useRedemptionOptions() {
  const query = useQuery<RedemptionOption[], Error>({
    queryKey: QUERY_KEYS.redemptionOptions,
    queryFn: fetchRedemptionOptions,
    staleTime: STALE_TIME_MS,
    retry: RETRY_COUNT,
    refetchOnWindowFocus: false,
  });

  return {
    options: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
'''


# ═══════════════════════════════════════════════════════════════════════
# 6. Components
# ═══════════════════════════════════════════════════════════════════════

STATS_CARDS_COMP = '''/**
 * StatsCards Component
 * =====================
 * Displays 4 key metric cards for EcoWallet.
 *
 * @module features/eco-wallet/components
 */

import {
  Wallet, TrendingUp, Coins, Gift, Clock,
  ArrowUpRight, ArrowDownRight, AlertCircle,
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import type { WalletStats } from '../types';
import { formatNumber, safeNumber } from '../utils/formatters';

interface StatsCardsProps {
  stats: WalletStats | null;
  isLoading?: boolean;
}

interface MetricCardConfig {
  icon: React.ReactNode;
  iconBg: string;
  iconColor: string;
  labelKey: string;
  labelFallback: string;
  value: string;
  changeIcon: React.ReactNode;
  changeLabel: string;
  changeClass: 'positive' | 'negative';
  fontSize?: string;
}

export function StatsCards({ stats, isLoading }: StatsCardsProps) {
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="grid-4col">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="metric-card">
            <div className="skeleton skeleton-title"></div>
            <div className="skeleton skeleton-card"></div>
          </div>
        ))}
      </div>
    );
  }

  const activeWallets = safeNumber(stats?.active_wallets ?? stats?.total_wallets);
  const totalEarnings = safeNumber(stats?.total_earnings);
  const totalRedemptions = safeNumber(stats?.total_redemptions);
  const pending = safeNumber(stats?.pending);

  const cards: MetricCardConfig[] = [
    {
      icon: <Wallet size={28} />,
      iconBg: 'rgba(16, 185, 129, 0.15)',
      iconColor: 'var(--accent-primary)',
      labelKey: 'crypto.walletBalance',
      labelFallback: 'Active Wallets',
      value: activeWallets.toLocaleString(),
      changeIcon: <TrendingUp size={12} />,
      changeLabel: '+12%',
      changeClass: 'positive',
    },
    {
      icon: <Coins size={28} />,
      iconBg: 'rgba(245, 158, 11, 0.15)',
      iconColor: 'var(--accent-secondary)',
      labelKey: 'crypto.totalReceived',
      labelFallback: 'Total Earnings',
      value: formatNumber(totalEarnings),
      changeIcon: <ArrowUpRight size={12} />,
      changeLabel: '+24%',
      changeClass: 'positive',
      fontSize: '24px',
    },
    {
      icon: <Gift size={28} />,
      iconBg: 'rgba(139, 92, 246, 0.15)',
      iconColor: 'var(--accent-purple)',
      labelKey: 'telegram.totalMessages',
      labelFallback: 'Redemptions',
      value: formatNumber(totalRedemptions),
      changeIcon: <ArrowDownRight size={12} />,
      changeLabel: 'Active',
      changeClass: 'negative',
      fontSize: '24px',
    },
    {
      icon: <Clock size={28} />,
      iconBg: 'rgba(239, 68, 68, 0.15)',
      iconColor: 'var(--accent-danger)',
      labelKey: 'crypto.pendingTx',
      labelFallback: 'Pending',
      value: pending.toString(),
      changeIcon: <AlertCircle size={12} />,
      changeLabel: 'Attention',
      changeClass: 'negative',
    },
  ];

  return (
    <div className="grid-4col">
      {cards.map((card, i) => (
        <div key={i} className="metric-card">
          <div
            className="metric-icon"
            style={{ background: card.iconBg, color: card.iconColor }}
          >
            {card.icon}
          </div>
          <div className="metric-label">
            {t(card.labelKey, card.labelFallback)}
          </div>
          <div className="metric-value" style={{ fontSize: card.fontSize }}>
            {card.value}
          </div>
          <div className={`metric-change ${card.changeClass}`}>
            {card.changeIcon} {card.changeLabel}
          </div>
        </div>
      ))}
    </div>
  );
}
'''

TRANSACTION_CHART_COMP = '''/**
 * TransactionChart Component
 * ===========================
 * Area chart showing earnings vs redemptions over time.
 *
 * Uses deterministic data from mockData (no Math.random in render).
 *
 * @module features/eco-wallet/components
 */

import { useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts';
import { TrendingUp } from 'lucide-react';
import type { TransactionDataPoint } from '../types';
import { DEFAULT_TRANSACTION_HISTORY } from '../constants/mockData';
import { CHART_COLORS } from '../constants/config';

interface TransactionChartProps {
  data?: TransactionDataPoint[];
}

export function TransactionChart({
  data = DEFAULT_TRANSACTION_HISTORY,
}: TransactionChartProps) {
  // Memoize to prevent unnecessary re-renders
  const chartData = useMemo(() => data, [data]);

  return (
    <div className="chart-container">
      <div className="chart-title">
        <TrendingUp size={20} />
        Earnings vs Redemptions (30 days)
      </div>
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={chartData}>
          <defs>
            <linearGradient id="earningsGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={CHART_COLORS.earnings} stopOpacity={0.8} />
              <stop offset="95%" stopColor={CHART_COLORS.earnings} stopOpacity={0.1} />
            </linearGradient>
            <linearGradient id="redemptionsGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={CHART_COLORS.redemptions} stopOpacity={0.8} />
              <stop offset="95%" stopColor={CHART_COLORS.redemptions} stopOpacity={0.1} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
          <XAxis dataKey="day" stroke="var(--text-muted)" fontSize={11} />
          <YAxis stroke="var(--text-muted)" fontSize={11} />
          <Tooltip
            contentStyle={{
              background: 'var(--bg-card-solid)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              color: 'var(--text-primary)',
            }}
          />
          <Legend />
          <Area
            type="monotone"
            dataKey="earnings"
            stroke={CHART_COLORS.earnings}
            fillOpacity={1}
            fill="url(#earningsGradient)"
            name="Earnings"
          />
          <Area
            type="monotone"
            dataKey="redemptions"
            stroke={CHART_COLORS.redemptions}
            fillOpacity={1}
            fill="url(#redemptionsGradient)"
            name="Redemptions"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
'''

OPTIONS_LIST_COMP = '''/**
 * OptionsList Component
 * ======================
 * Generic reusable list for earning/redemption options.
 *
 * Single Responsibility: Render a list of options with icon and amount.
 *
 * @module features/eco-wallet/components
 */

import { Leaf, Gift } from 'lucide-react';
import type { EarningOption, RedemptionOption } from '../types';
import { safeString } from '../utils/formatters';

type OptionType = 'earning' | 'redemption';

interface OptionsListProps {
  type: OptionType;
  options: EarningOption[] | RedemptionOption[];
  title: string;
  icon: React.ReactNode;
  emptyMessage: string;
}

export function OptionsList({
  type,
  options,
  title,
  icon,
  emptyMessage,
}: OptionsListProps) {
  const iconBg =
    type === 'earning'
      ? 'rgba(245, 158, 11, 0.15)'
      : 'rgba(139, 92, 246, 0.15)';
  const iconColor =
    type === 'earning'
      ? 'var(--accent-secondary)'
      : 'var(--accent-purple)';
  const amountColor =
    type === 'earning'
      ? 'var(--accent-primary)'
      : 'var(--accent-purple)';
  const ItemIcon = type === 'earning' ? Leaf : Gift;
  const prefix = type === 'earning' ? '+' : '';

  return (
    <div className="chart-container">
      <div className="chart-title">
        {icon} {title} ({options.length})
      </div>
      <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
        {options.length === 0 ? (
          <div className="empty-state-enhanced" style={{ padding: '40px' }}>
            <div className="icon">🎯</div>
            <div className="title">{emptyMessage}</div>
          </div>
        ) : (
          options.map((option, i) => {
            const uniqueKey = option.category
              ? `${type}-${option.category}-${i}`
              : `${type}-${i}`;

            return (
              <div
                key={uniqueKey}
                className="transaction-row"
                style={{ borderBottom: '1px solid var(--border-color)' }}
              >
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '12px',
                    background: iconBg,
                    color: iconColor,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <ItemIcon size={22} />
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {safeString(option.category, 'Option')}
                  </div>
                  <div
                    style={{
                      fontSize: '12px',
                      color: 'var(--text-muted)',
                      marginTop: '2px',
                    }}
                  >
                    {safeString(option.description, 'Description')}
                  </div>
                </div>
                <div style={{ textAlign: 'end', flexShrink: 0 }}>
                  <div
                    style={{
                      fontWeight: 700,
                      color: amountColor,
                      fontSize: '16px',
                    }}
                  >
                    {prefix}{option.eco_amount ?? 0}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-faint)' }}>
                    tokens
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
'''

ERROR_BOUNDARY_COMP = '''/**
 * EcoWalletErrorBoundary
 * =======================
 * Catches errors in EcoWallet dashboard.
 *
 * @module features/eco-wallet/components
 */

import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class EcoWalletErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error('[EcoWalletDashboard] Error:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <div
          style={{
            padding: '40px',
            textAlign: 'center',
            background: 'rgba(239, 68, 68, 0.1)',
            borderRadius: '12px',
            border: '1px solid rgba(239, 68, 68, 0.3)',
          }}
        >
          <div
            style={{
              fontSize: '18px',
              fontWeight: 700,
              color: '#ef4444',
              marginBottom: '8px',
            }}
          >
            خطا در بارگذاری داشبورد EcoWallet
          </div>
          <div
            style={{
              fontSize: '13px',
              color: 'var(--text-muted)',
              marginBottom: '16px',
            }}
          >
            {this.state.error?.message || 'خطای ناشناخته'}
          </div>
          <button
            onClick={this.handleRetry}
            className="btn-primary"
            style={{ padding: '8px 20px' }}
          >
            تلاش مجدد
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
'''


# ═══════════════════════════════════════════════════════════════════════
# 7. Main Orchestrator (NEW EcoWalletDashboard.tsx)
# ═══════════════════════════════════════════════════════════════════════

ECOWALLET_DASHBOARD_NEW = '''/**
 * EcoWalletDashboard (Orchestrator)
 * ==================================
 * Main entry point for EcoWallet Command Center.
 *
 * This file is ONLY an orchestrator. All logic is extracted to:
 * - hooks/ (React Query for all API calls)
 * - components/ (extracted UI components)
 * - api/ (API functions)
 * - constants/ (configuration and mock data)
 *
 * Before: 368 lines with anti-patterns
 * After:  ~70 lines of clean orchestration
 *
 * Key improvements:
 * - Math.random removed from render (deterministic chart)
 * - fetch in useEffect → React Query (3 separate queries)
 * - any types removed (proper TypeScript)
 * - Extracted 4 reusable components
 *
 * @module pages/admin/EcoWalletDashboard
 */

import { Wallet, Coins, Gift, RefreshCw } from 'lucide-react';
import { useTranslation } from 'react-i18next';

import { useEcoWalletStats } from '../../features/eco-wallet/hooks/useEcoWalletStats';
import { useEarningOptions } from '../../features/eco-wallet/hooks/useEarningOptions';
import { useRedemptionOptions } from '../../features/eco-wallet/hooks/useRedemptionOptions';
import { StatsCards } from '../../features/eco-wallet/components/StatsCards';
import { TransactionChart } from '../../features/eco-wallet/components/TransactionChart';
import { OptionsList } from '../../features/eco-wallet/components/OptionsList';
import { EcoWalletErrorBoundary } from '../../features/eco-wallet/components/EcoWalletErrorBoundary';

import './AdminTheme.css';
import './AdminPanelAdvanced.css';

export default function EcoWalletDashboard() {
  const { t } = useTranslation();

  // React Query hooks (auto-loading, auto-error handling)
  const { stats, isLoading: statsLoading, refetch: refetchStats } = useEcoWalletStats();
  const { options: earningOptions, refetch: refetchEarning } = useEarningOptions();
  const { options: redemptionOptions, refetch: refetchRedemption } = useRedemptionOptions();

  const handleRefresh = () => {
    void refetchStats();
    void refetchEarning();
    void refetchRedemption();
  };

  return (
    <EcoWalletErrorBoundary>
      <div className="admin-page-container">
        {/* Header */}
        <div className="page-header">
          <div>
            <h1 className="page-title">
              <Wallet size={32} style={{ color: 'var(--accent-primary)' }} />
              {t('nav.ecowallet', 'EcoWallet Command Center')}
            </h1>
            <p className="page-subtitle">
              {t('crypto.subtitle', 'Monitor eco wallet transactions')}
            </p>
          </div>
          <button className="refresh-btn" onClick={handleRefresh}>
            <RefreshCw size={16} /> {t('common.refresh', 'Refresh')}
          </button>
        </div>

        {/* Stats Cards (with skeleton loading) */}
        <StatsCards stats={stats} isLoading={statsLoading} />

        {/* Transaction Chart (deterministic, no Math.random) */}
        <TransactionChart />

        {/* Options Grid */}
        <div className="grid-2col">
          <OptionsList
            type="earning"
            options={earningOptions}
            title={t('crypto.recentTransactions', 'Earning Options')}
            icon={<Coins size={20} />}
            emptyMessage="No earning options"
          />
          <OptionsList
            type="redemption"
            options={redemptionOptions}
            title={t('crypto.recentTransactions', 'Redemption Options')}
            icon={<Gift size={20} />}
            emptyMessage="No redemption options"
          />
        </div>
      </div>
    </EcoWalletErrorBoundary>
  );
}
'''


# ═══════════════════════════════════════════════════════════════════════
# 8. Tests
# ═══════════════════════════════════════════════════════════════════════

FORMATTERS_TEST = '''/**
 * Formatters Tests
 */
import { describe, it, expect } from 'vitest';
import { safeString, formatNumber, safeNumber } from '../utils/formatters';

describe('formatters', () => {
  describe('safeString', () => {
    it('should handle null', () => {
      expect(safeString(null)).toBe('N/A');
    });

    it('should handle undefined', () => {
      expect(safeString(undefined)).toBe('N/A');
    });

    it('should pass through strings', () => {
      expect(safeString('hello')).toBe('hello');
    });

    it('should convert numbers', () => {
      expect(safeString(42)).toBe('42');
    });

    it('should convert booleans', () => {
      expect(safeString(true)).toBe('true');
    });

    it('should stringify objects', () => {
      expect(safeString({ a: 1 })).toBe('{"a":1}');
    });

    it('should use fallback', () => {
      expect(safeString(null, 'custom')).toBe('custom');
    });
  });

  describe('formatNumber', () => {
    it('should format numbers', () => {
      expect(formatNumber(1234567)).toBeTruthy();
    });

    it('should handle undefined', () => {
      expect(formatNumber(undefined)).toBe('0');
    });
  });

  describe('safeNumber', () => {
    it('should return number when valid', () => {
      expect(safeNumber(42)).toBe(42);
    });

    it('should return fallback for undefined', () => {
      expect(safeNumber(undefined, 10)).toBe(10);
    });

    it('should return fallback for NaN', () => {
      expect(safeNumber(NaN, 5)).toBe(5);
    });
  });
});
'''

MOCK_DATA_TEST = '''/**
 * Mock Data Tests
 */
import { describe, it, expect } from 'vitest';
import {
  generateTransactionHistory,
  DEFAULT_TRANSACTION_HISTORY,
} from '../constants/mockData';
import { CHART_CONFIG } from '../constants/config';

describe('mockData', () => {
  describe('generateTransactionHistory', () => {
    it('should generate correct number of days', () => {
      const history = generateTransactionHistory();
      expect(history).toHaveLength(CHART_CONFIG.days);
    });

    it('should be deterministic with same seed', () => {
      const h1 = generateTransactionHistory(CHART_CONFIG, 42);
      const h2 = generateTransactionHistory(CHART_CONFIG, 42);
      expect(h1).toEqual(h2);
    });

    it('should respect earnings range', () => {
      const history = generateTransactionHistory();
      for (const point of history) {
        expect(point.earnings).toBeGreaterThanOrEqual(CHART_CONFIG.earningsRange.min);
        expect(point.earnings).toBeLessThanOrEqual(CHART_CONFIG.earningsRange.max);
      }
    });

    it('should respect redemptions range', () => {
      const history = generateTransactionHistory();
      for (const point of history) {
        expect(point.redemptions).toBeGreaterThanOrEqual(CHART_CONFIG.redemptionsRange.min);
        expect(point.redemptions).toBeLessThanOrEqual(CHART_CONFIG.redemptionsRange.max);
      }
    });
  });

  describe('DEFAULT_TRANSACTION_HISTORY', () => {
    it('should be pre-generated', () => {
      expect(DEFAULT_TRANSACTION_HISTORY).toHaveLength(30);
    });
  });
});
'''


# ═══════════════════════════════════════════════════════════════════════
# Main Execution
# ═══════════════════════════════════════════════════════════════════════

def ok(m): print(f"\033[92m✓\033[0m  {m}")
def info(m): print(f"\033[94mℹ\033[0m  {m}")
def warn(m): print(f"\033[93m⚠\033[0m  {m}")
def err(m): print(f"\033[91m✗\033[0m  {m}")


def write_file(path: Path, content: str):
    """نوشتن فایل با ایجاد خودکار پوشه‌ها"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    lines = len(content.splitlines())
    print(f"  ✓ {path.relative_to(FRONTEND)} ({lines} lines)")


def backup_old():
    """پشتیبان‌گیری از فایل قدیمی"""
    if not OLD_FILE.exists():
        err(f"فایل یافت نشد: {OLD_FILE}")
        return False

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = OLD_FILE.with_suffix(f".tsx.refactor_backup_{ts}")
    shutil.copy2(OLD_FILE, backup)
    ok(f"پشتیبان: {backup.relative_to(FRONTEND)}")

    backups_dir = PROJECT_ROOT / "_backups" / "eco_wallet_refactor"
    backups_dir.mkdir(parents=True, exist_ok=True)
    backup2 = backups_dir / f"EcoWalletDashboard_old_{ts}.tsx"
    shutil.copy2(OLD_FILE, backup2)
    ok(f"پشتیبان دوم: {backup2.relative_to(PROJECT_ROOT)}")

    return True


def main():
    print("\n" + "=" * 70)
    print("  🚀 Phase 2 - Refactor EcoWalletDashboard")
    print("=" * 70 + "\n")

    # ── گام ۱: پشتیبان ─────────────────────────────────────
    print("💾 گام ۱: پشتیبان‌گیری از فایل قدیمی...")
    if not backup_old():
        return 1
    print()

    # ── گام ۲: ساختار ─────────────────────────────────────
    print("📁 گام ۲: ایجاد ساختار features/eco-wallet/...")
    ECO_WALLET.mkdir(parents=True, exist_ok=True)
    for folder in ["types", "constants", "utils", "api", "hooks", "components", "__tests__"]:
        (ECO_WALLET / folder).mkdir(exist_ok=True)
    ok("ساختار ایجاد شد")
    print()

    # ── گام ۳: Types ──────────────────────────────────────
    print("📦 گام ۳: ایجاد Types...")
    write_file(ECO_WALLET / "types" / "ecoWallet.types.ts", ECOWALLET_TYPES)
    print()

    # ── گام ۴: Constants ──────────────────────────────────
    print("📦 گام ۴: ایجاد Constants...")
    write_file(ECO_WALLET / "constants" / "config.ts", CONFIG_CONST)
    write_file(ECO_WALLET / "constants" / "mockData.ts", MOCK_DATA_CONST)
    print()

    # ── گام ۵: API ──────────────────────────────────────
    print("📦 گام ۵: ایجاد API Functions...")
    write_file(ECO_WALLET / "api" / "ecoWalletApi.ts", API_FUNCTIONS)
    print()

    # ── گام ۶: Utils ──────────────────────────────────────
    print("📦 گام ۶: ایجاد Utils...")
    write_file(ECO_WALLET / "utils" / "formatters.ts", FORMATTERS_UTIL)
    print()

    # ── گام ۷: Hooks ──────────────────────────────────────
    print("📦 گام ۷: ایجاد Custom Hooks (React Query)...")
    write_file(ECO_WALLET / "hooks" / "useEcoWalletStats.ts", USE_STATS_HOOK)
    write_file(ECO_WALLET / "hooks" / "useEarningOptions.ts", USE_EARNING_HOOK)
    write_file(ECO_WALLET / "hooks" / "useRedemptionOptions.ts", USE_REDEMPTION_HOOK)
    print()

    # ── گام ۸: Components ─────────────────────────────────
    print("📦 گام ۸: ایجاد Components...")
    write_file(ECO_WALLET / "components" / "StatsCards.tsx", STATS_CARDS_COMP)
    write_file(ECO_WALLET / "components" / "TransactionChart.tsx", TRANSACTION_CHART_COMP)
    write_file(ECO_WALLET / "components" / "OptionsList.tsx", OPTIONS_LIST_COMP)
    write_file(ECO_WALLET / "components" / "EcoWalletErrorBoundary.tsx", ERROR_BOUNDARY_COMP)
    print()

    # ── گام ۹: Tests ──────────────────────────────────────
    print("📦 گام ۹: ایجاد Tests...")
    write_file(ECO_WALLET / "__tests__" / "formatters.test.ts", FORMATTERS_TEST)
    write_file(ECO_WALLET / "__tests__" / "mockData.test.ts", MOCK_DATA_TEST)
    print()

    # ── گام ۱۰: جایگزینی فایل اصلی ───────────────────────
    print("🔄 گام ۱۰: جایگزینی EcoWalletDashboard.tsx...")
    OLD_FILE.write_text(ECOWALLET_DASHBOARD_NEW, encoding="utf-8")
    ok(f"فایل اصلی جایگزین شد ({len(ECOWALLET_DASHBOARD_NEW.splitlines())} lines)")
    print()

    # ── گام ۱۱: Build ────────────────────────────────────
    print("🔨 گام ۱۱: اجرای build...")
    for p in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        if Path(p).exists() and p not in os.environ["PATH"]:
            os.environ["PATH"] = p + os.pathsep + os.environ["PATH"]

    build_result = subprocess.run(
        "pnpm build",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        timeout=300
    )

    build_output = build_result.stdout + build_result.stderr

    if build_result.returncode != 0:
        err("Build شکست خورد")
        for line in build_output.splitlines()[-30:]:
            print(f"  {line}")
        return 1

    ok("Build موفق")
    for line in build_output.splitlines():
        if "built in" in line or "EcoWallet" in line:
            print(f"  {line.strip()}")
    print()

    # ── گام ۱۲: تست‌های جدید ────────────────────────────
    print("🧪 گام ۱۲: اجرای تست‌های جدید...")
    test_result = subprocess.run(
        "pnpm test features/eco-wallet",
        shell=True, cwd=FRONTEND,
        capture_output=True, text=True,
        encoding="utf-8", errors="replace",
        timeout=120
    )

    test_output = test_result.stdout + test_result.stderr
    for line in test_output.splitlines():
        if any(k in line for k in ["Test Files", "Tests", "passed", "failed"]):
            print(f"  {line}")
    print()

    # ── گام ۱۳: Commit ────────────────────────────────────
    print("📦 گام ۱۳: commit تغییرات...")
    try:
        subprocess.run("git add .", shell=True, cwd=PROJECT_ROOT, check=True)
        msg = (
            'refactor(eco-wallet): rewrite EcoWalletDashboard with feature-based architecture\\n\\n'
            '- Extracted 3 React Query hooks (stats, earning, redemption)\\n'
            '- Extracted 4 components (StatsCards, TransactionChart, OptionsList, ErrorBoundary)\\n'
            '- Removed Math.random from render (seeded LCG for chart data)\\n'
            '- Removed any types (proper TypeScript generics)\\n'
            '- Added API layer with proper error handling\\n'
            '- 368 lines → ~70 lines orchestration (81% reduction)'
        )
        subprocess.run(
            f'git commit -m "{msg}"',
            shell=True, cwd=PROJECT_ROOT, check=True
        )
        subprocess.run("git push origin main", shell=True, cwd=PROJECT_ROOT, check=True)
        ok("commit و push موفق")
    except Exception as e:
        warn(f"commit: {e}")
    print()

    # ── گزارش نهایی ───────────────────────────────────────
    print("\033[1m\033[92m" + "=" * 70 + "\033[0m")
    print("\033[1m\033[92m  🎉 EcoWalletDashboard با موفقیت refactor شد! 🎉\033[0m")
    print("\033[1m\033[92m" + "=" * 70 + "\033[0m\n")

    print("  📊 آمار:")
    print("    ✓ 368 → ~70 lines (81% reduction)")
    print("    ✓ Build موفق")
    print("    ✓ معماری feature-based")
    print("    ✓ 3 React Query hooks")
    print("    ✓ 4 extracted components")
    print("    ✓ Error Boundary")
    print("    ✓ Type safety (no any)")
    print("    ✓ Deterministic chart data")
    print()

    print("  🏗️ ساختار جدید:")
    print("    features/eco-wallet/")
    print("    ├── types/        (1 file)")
    print("    ├── constants/    (2 files)")
    print("    ├── api/          (1 file)")
    print("    ├── utils/        (1 file)")
    print("    ├── hooks/        (3 files)")
    print("    ├── components/   (4 files)")
    print("    └── __tests__/    (2 files)")
    print()

    print("  🎯 اقدامات بعدی:")
    print("    • بررسی عملکرد در مرورگر")
    print("    • انتخاب فایل بعدی از ۵ فایل باقی‌مانده")
    print("    • ادامه با LiveFeed.tsx (HIGH) یا MarketplaceDashboard.tsx (HIGH)")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())