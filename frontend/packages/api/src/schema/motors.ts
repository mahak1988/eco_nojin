import { z } from 'zod';

export const MotorKindSchema = z.enum([
  'swat',
  'rusle',
  'aquacrop',
  'rothc',
  'pywr',
  'hecras',
  'optimize',
]);
export type MotorKind = z.infer<typeof MotorKindSchema>;

export const MotorRunRequestSchema = z.object({
  motor: MotorKindSchema,
  payload: z.record(z.string(), z.unknown()),
  dry_run: z.boolean(),
});
export type MotorRunRequest = z.infer<typeof MotorRunRequestSchema>;

export const MotorRunResultSchema = z.object({
  motor: MotorKindSchema,
  duration_ms: z.number(),
  cached: z.boolean(),
  output: z.record(z.string(), z.unknown()),
});
export type MotorRunResult = z.infer<typeof MotorRunResultSchema>;

export const MotorChainRequestSchema = z.object({
  chain: z.array(MotorKindSchema).min(1),
  payload: z.record(z.string(), z.unknown()),
});
export type MotorChainRequest = z.infer<typeof MotorChainRequestSchema>;

export const MotorChainResultSchema = z.object({
  duration_ms: z.number(),
  steps: z.array(MotorRunResultSchema),
});
export type MotorChainResult = z.infer<typeof MotorChainResultSchema>;

export const MotorKind = MotorKindSchema;
export const MotorRunRequest = MotorRunRequestSchema;
export const MotorRunResult = MotorRunResultSchema;
export const MotorChainRequest = MotorChainRequestSchema;
export const MotorChainResult = MotorChainResultSchema;