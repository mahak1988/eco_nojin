/** Issuance types — carbon credit creation, registry, and gate tracking.
 * All values are simulation/pre-verification status indicators. */

export type IssuancePhase = 'phase1_utility' | 'phase2_carbon';

export type VerificationLabel = 'modeled_estimate' | 'field_verified' | 'not_certified';

export type GateType = 'VVB' | 'registry' | 'legal';

export interface GateStatus {
  gate: GateType;
  status: 'pending' | 'passed' | 'skipped';
  note?: string;
}

export interface IssuanceRecord {
  id: string;
  projectId: string;
  phase: IssuancePhase;
  verificationLabel: VerificationLabel;
  gates: GateStatus[];
  simulatedAmount: number;
  unit: string;
  freezeStatus: 'active' | 'frozen' | 'retired';
  retirementStatus: 'active' | 'retired' | 'pending';
  idempotencyKey: string | null;
  registryEntry: 'simulated' | 'pending';
  verificationLabel: VerificationLabel;
  methodology: string;
  createdAt: string;
  updatedAt: string;
}

export interface IssuanceListResponse {
  records: IssuanceRecord[];
  total: number;
  simulationOnly: boolean;
}

export interface IssuanceCreateRequest {
  projectId: string;
  methodology: string;
  simulatedAmount: number;
  idempotencyKey: string;
}

export interface IssuanceCreateResponse {
  id: string;
  status: 'simulated';
  verificationLabel: VerificationLabel;
  gates: GateStatus[];
  idempotencyKey: string;
}
