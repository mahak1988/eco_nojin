import type { MotorKind } from '@eco/api/schema/motors';

export type ModelDomain =
  | 'soil'
  | 'water'
  | 'crop'
  | 'carbon'
  | 'climate'
  | 'erosion'
  | 'optimization'
  | 'hydraulic';

export type ModelMeta = {
  id: MotorKind;
  name: string;
  domain: ModelDomain;
  description: string;
  version: string;
  source: 'real' | 'mock' | 'external';
  externalBinary?: string;
  /** Average runtime in milliseconds on master DB. */
  avg_runtime_ms: number;
};

export type ModelRunInput = Record<string, unknown>;

export type ModelRunOutput<T = unknown> = {
  motor: MotorKind;
  output: T;
  duration_ms: number;
  cached: boolean;
};

export type ModelRunner<TInput extends ModelRunInput, TOutput> = {
  meta: ModelMeta;
  validate: (input: unknown) => TInput;
  run: (input: TInput) => Promise<ModelRunOutput<TOutput>>;
};