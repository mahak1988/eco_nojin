/**
 * Eco Nojin - تنظیمات پرداخت کریپتویی
 *═══════════════════════════════════════════════════════════════════════
 * آدرس‌های کیف پول پروژه و اطلاعات شبکه‌های پشتیبانی‌شده
 */

export interface CryptoNetwork {
  id: string;
  name: string;
  nameFa: string;
  symbol: string;
  chainId: number | string;
  color: string;
  icon: string;
  explorerUrl: string;
  rpcUrl: string;
  /** آدرس USDT contract در این شبکه */
  usdtContract: string;
  /** آدرس کیف پول پروژه */
  projectAddress: string;
  /** تعداد confirmations لازم */
  confirmations: number;
  /** کارمزد تخمینی (USD) */
  estimatedFeeUsd: number;
}

export const CRYPTO_NETWORKS: CryptoNetwork[] = [
  {
    id: 'trc20',
    name: 'Tron (TRC20)',
    nameFa: 'ترون (TRC20)',
    symbol: 'USDT-TRC20',
    chainId: 'tron',
    color: '#FF0013',
    icon: '⚡',
    explorerUrl: 'https://tronscan.org/#/tx/',
    rpcUrl: 'https://api.trongrid.io',
    // USDT on Tron
    usdtContract: 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t',
    // آدرس پروژه - تغییر دهید به آدرس واقعی
    projectAddress: 'TYourProjectAddressHere123456789ABCDEF',
    confirmations: 20,
    estimatedFeeUsd: 1,
  },
  {
    id: 'erc20',
    name: 'Ethereum (ERC20)',
    nameFa: 'اتریوم (ERC20)',
    symbol: 'USDT-ERC20',
    chainId: 1,
    color: '#627EEA',
    icon: 'Ξ',
    explorerUrl: 'https://etherscan.io/tx/',
    rpcUrl: 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY',
    usdtContract: '0xdAC17F958D2ee523a2206206994597C13D831ec7',
    projectAddress: '0xYourProjectAddressHere1234567890ABCDEF12',
    confirmations: 12,
    estimatedFeeUsd: 5,
  },
  {
    id: 'bep20',
    name: 'BNB Smart Chain (BEP20)',
    nameFa: 'بایننس اسمارت چین (BEP20)',
    symbol: 'USDT-BEP20',
    chainId: 56,
    color: '#F3BA2F',
    icon: '🔶',
    explorerUrl: 'https://bscscan.com/tx/',
    rpcUrl: 'https://bsc-dataseed.binance.org',
    usdtContract: '0x55d398326f99059fF775485246999027B3197955',
    projectAddress: '0xYourProjectAddressHere1234567890ABCDEF12',
    confirmations: 15,
    estimatedFeeUsd: 0.3,
  },
  {
    id: 'polygon',
    name: 'Polygon',
    nameFa: 'پلیگان',
    symbol: 'USDT-POLYGON',
    chainId: 137,
    color: '#8247E5',
    icon: '🟣',
    explorerUrl: 'https://polygonscan.com/tx/',
    rpcUrl: 'https://polygon-rpc.com',
    usdtContract: '0xc2132D05D31c914a87C6611C10748AEb04B58e8F',
    projectAddress: '0xYourProjectAddressHere1234567890ABCDEF12',
    confirmations: 128,
    estimatedFeeUsd: 0.01,
  },
];

/**
 * ABI استاندارد ERC20 برای USDT transfers
 */
export const ERC20_ABI = [
  {
    constant: false,
    inputs: [
      { name: '_to', type: 'address' },
      { name: '_value', type: 'uint256' },
    ],
    name: 'transfer',
    outputs: [{ name: '', type: 'bool' }],
    type: 'function',
  },
  {
    constant: true,
    inputs: [{ name: '_owner', type: 'address' }],
    name: 'balanceOf',
    outputs: [{ name: 'balance', type: 'uint256' }],
    type: 'function',
  },
  {
    constant: true,
    inputs: [],
    name: 'decimals',
    outputs: [{ name: '', type: 'uint8' }],
    type: 'function',
  },
  {
    constant: true,
    inputs: [],
    name: 'symbol',
    outputs: [{ name: '', type: 'string' }],
    type: 'function',
  },
];

/**
 * پلن‌های اشتراک
 */
export interface SubscriptionPlan {
  id: string;
  name: string;
  nameFa: string;
  priceUsd: number;
  period: 'monthly' | 'yearly' | 'lifetime';
  features: string[];
  recommended?: boolean;
  color: string;
}

export const SUBSCRIPTION_PLANS: SubscriptionPlan[] = [
  {
    id: 'starter',
    name: 'Starter',
    nameFa: 'شروع',
    priceUsd: 9,
    period: 'monthly',
    features: [
      'دسترسی به ۵ ماژول پایه',
      '۱ مزرعه',
      'گزارش‌های ماهانه',
      'پشتیبانی ایمیلی',
    ],
    color: '#10b981',
  },
  {
    id: 'farmer',
    name: 'Farmer Pro',
    nameFa: 'کشاورز حرفه‌ای',
    priceUsd: 29,
    period: 'monthly',
    features: [
      'دسترسی به تمام ماژول‌ها',
      '۱۰ مزرعه',
      'شبیه‌سازهای پیشرفته',
      'تحلیل ماهواره‌ای',
      'پشتیبانی اولویت‌دار',
    ],
    recommended: true,
    color: '#3b82f6',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    nameFa: 'سازمانی',
    priceUsd: 249,
    period: 'monthly',
    features: [
      'مزارع نامحدود',
      'API اختصاصی',
      'White-label',
      'پشتیبانی ۲۴/۷',
      'مشاوره تخصصی',
    ],
    color: '#8b5cf6',
  },
  {
    id: 'lifetime',
    name: 'Lifetime',
    nameFa: 'مادام‌العمر',
    priceUsd: 499,
    period: 'lifetime',
    features: [
      'دسترسی مادام‌العمر',
      'تمام ویژگی‌های Enterprise',
      'به‌روزرسانی‌های رایگان',
      'عضویت در جامعه VIP',
    ],
    color: '#f59e0b',
  },
];
