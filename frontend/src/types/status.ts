/** Status types — service health and operational status.
 * All values reflect real probing or simulation indicators. */

export type ServiceStatus = 'online' | 'offline' | 'degraded' | 'checking';

export interface HealthStatus {
  gateway: ServiceStatus;
  latencyMs: number | null;
  checkedAt: string;
  services: Record<string, ServiceStatus>;
  simulationMode: boolean;
}

export interface FreezeStatus {
  accountId: string;
  status: 'active' | 'frozen';
  frozenBy: string | null;
  frozenAt: string | null;
  reason: string | null;
  judicialOrderRef: string | null;
}

export interface RetirementStatus {
  creditId: string;
  status: 'active' | 'retired' | 'pending';
  retiredAt: string | null;
  reason: string | null;
}

export interface IdempotencyStatus {
  key: string;
  requestHash: string;
  status: 'pending' | 'completed' | 'failed';
  responseCode: number | null;
  createdAt: string;
  expiresAt: string;
}

export interface StatusSummary {
  health: HealthStatus;
  freezeStatus: FreezeStatus;
  retirementStatus: RetirementStatus;
  idempotency: IdempotencyStatus[];
  simulationMode: boolean;
}
