export type DataStatus = 'live' | 'demo' | 'stale' | 'unavailable';

export type DataSourceKind = 'api' | 'dataset' | 'model' | 'document' | 'manual' | 'demo';

export interface ProvenanceReference {
  kind: DataSourceKind;
  id: string;
  uri?: string;
  observedAt: string;
  version?: string;
  license?: string;
  verified: boolean;
}

export interface DataEnvelopeError {
  code: string;
  message: string;
  retryable: boolean;
}

interface DataEnvelopeBase {
  source: ProvenanceReference;
  observedAt: string;
  version?: string;
  confidence?: number;
  unit?: string;
  provenance: ProvenanceReference[];
}

export type DataEnvelope<T> = DataEnvelopeBase &
  (
    | { status: Exclude<DataStatus, 'unavailable'>; data: T }
    | { status: 'unavailable'; data: null; error: DataEnvelopeError }
  );

export interface CreateDataEnvelopeInput<T> {
  status: DataStatus;
  data: T | null;
  source: ProvenanceReference;
  observedAt: string;
  version?: string;
  confidence?: number;
  unit?: string;
  provenance?: ProvenanceReference[];
  error?: DataEnvelopeError;
}

function assertIsoDate(value: string): void {
  if (Number.isNaN(Date.parse(value))) {
    throw new Error(`Invalid ISO date: ${value}`);
  }
}

function assertConfidence(value: number | undefined): void {
  if (value !== undefined && (value < 0 || value > 1)) {
    throw new Error('Confidence must be between 0 and 1');
  }
}

export function createDataEnvelope<T>(input: CreateDataEnvelopeInput<T>): DataEnvelope<T> {
  assertIsoDate(input.observedAt);
  assertIsoDate(input.source.observedAt);
  assertConfidence(input.confidence);

  if (input.source.verified && input.status === 'demo') {
    throw new Error('Demo data cannot be marked verified');
  }

  if (input.status === 'unavailable') {
    if (input.data !== null) {
      throw new Error('Unavailable data must have a null data value');
    }
    if (!input.error) {
      throw new Error('Unavailable data requires an error');
    }
    return {
      status: 'unavailable',
      data: null,
      source: input.source,
      observedAt: input.observedAt,
      version: input.version,
      confidence: input.confidence,
      unit: input.unit,
      provenance: input.provenance ?? [input.source],
      error: input.error,
    };
  }

  if (input.data === null) {
    throw new Error('Live, demo and stale data require a data value');
  }

  return {
    status: input.status,
    data: input.data,
    source: input.source,
    observedAt: input.observedAt,
    version: input.version,
    confidence: input.confidence,
    unit: input.unit,
    provenance: input.provenance ?? [input.source],
  };
}

export function isDataEnvelope<T>(value: unknown): value is DataEnvelope<T> {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<DataEnvelope<T>>;
  return (
    typeof candidate.status === 'string' &&
    typeof candidate.observedAt === 'string' &&
    typeof candidate.source === 'object' &&
    candidate.source !== null &&
    Array.isArray(candidate.provenance)
  );
}
