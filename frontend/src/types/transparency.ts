/** Transparency types — data quality labels and provenance.
 * All values are simulation/pre-verification indicators. */

export type DataQualityLabel = 'modeled_estimate' | 'field_verified' | 'not_certified';

export interface DataQualityEntry {
  metricName: string;
  label: DataQualityLabel;
  source: string;
  method: string;
  standard: string;
  simulationNote: string;
}

export interface TransparencyReport {
  id: string;
  title: string;
  description: string;
  qualityLabel: DataQualityLabel;
  freezeStatus: 'active' | 'frozen';
  retirementStatus: 'active' | 'retired';
  idempotencyKey: string | null;
  simulatedData: boolean;
  methodology: string;
  createdAt: string;
}

export interface TransparencyStatus {
  totalReports: number;
  simulationMode: boolean;
  qualityLabels: Record<DataQualityLabel, number>;
  freezeCount: number;
  retirementCount: number;
  pendingIdempotencyCount: number;
}

export interface RegistryCheckResult {
  id: string;
  found: boolean;
  simulationMode: boolean;
  verificationLabel: DataQualityLabel;
  gates: { gate: string; status: string }[];
}
