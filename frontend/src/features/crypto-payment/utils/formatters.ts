/**
 * Formatters
 * ===========
 * Currency and address formatting utilities.
 *
 * @module features/crypto-payment/utils
 */

/**
 * Format number as USD currency
 */
export function formatUSD(value: number, maxDigits = 2): string {
  return value.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: maxDigits,
  });
}

/**
 * Format number as crypto amount (4 decimal places)
 */
export function formatCrypto(value: number): string {
  return value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  });
}

/**
 * Truncate address with ellipsis in the middle
 * Example: "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb"
 *       → "0x742d...f0bEb"
 */
export function truncateAddress(address: string, startChars = 6, endChars = 4): string {
  if (address.length <= startChars + endChars + 3) return address;
  return `${address.slice(0, startChars)}...${address.slice(-endChars)}`;
}

/**
 * Truncate transaction hash
 */
export function truncateHash(hash: string): string {
  return truncateAddress(hash, 10, 8);
}

/**
 * Format time as locale-specific time string
 */
export function formatTime(date: Date): string {
  return date.toLocaleTimeString();
}
