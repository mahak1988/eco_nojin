/**
 * Security Types
 * ===============
 * @module features/security/types
 */

/** Event severity */
export type Severity = 'low' | 'medium' | 'high' | 'critical';

/** Login event type */
export type EventType = 'Successful Login' | 'Failed Login' | 'Unknown';

/** Security event */
export interface SecurityEvent {
  id: string;
  type: EventType;
  detail: string;
  ip_address: string;
  created_at: string;
  severity: Severity;
}

/** Raw API event (before transformation) */
export interface RawSecurityEvent {
  id?: string;
  detail?: string;
  ip_address?: string;
  created_at?: string;
  [key: string]: unknown;
}

/** Hourly aggregated data for chart */
export interface HourlyData {
  hour: string;
  success: number;
  failed: number;
}

/** Derived statistics (memoized) */
export interface SecurityStats {
  totalEvents: number;
  successRate: string;
  successCount: number;
  failedCount: number;
  uniqueFailedIPs: number;
  securityScore: number;
  hourlyData: HourlyData[];
}
