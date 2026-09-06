/**
 * Static registry of well-known scientific models exposed by the backend.
 *
 * The backend advertises 318 model classes across 14 domains; only the most
 * commonly invoked ones are described statically here. New entries are
 * added at runtime via {@link registerModel} / fetched from
 * `GET /api/v1/models/list` through {@link loadRemoteModels}.
 */

import type { MotorKind } from '@eco/api/schema/motors';
import type { ModelMeta, ModelRunInput, ModelRunOutput } from './types';

const _meta = new Map<MotorKind, ModelMeta>();
const _runners = new Map<MotorKind, (input: ModelRunInput) => Promise<ModelRunOutput>>();

export function registerModel(
  meta: ModelMeta,
  runner?: (input: ModelRunInput) => Promise<ModelRunOutput>,
): void {
  _meta.set(meta.id, meta);
  if (runner) _runners.set(meta.id, runner);
}

export function listModels(): ModelMeta[] {
  return [..._meta.values()].sort((a, b) => a.name.localeCompare(b.name));
}

export function getModel(id: MotorKind): ModelMeta | undefined {
  return _meta.get(id);
}

export async function runModelLocally(
  id: MotorKind,
  input: ModelRunInput,
): Promise<ModelRunOutput> {
  const runner = _runners.get(id);
  if (!runner) throw new Error(`No local runner registered for ${id}`);
  return runner(input);
}

export function modelsByDomain(domain: ModelMeta['domain']): ModelMeta[] {
  return listModels().filter((m) => m.domain === domain);
}

/** Total known classes (advisory; backend may expose more). */
export const TOTAL_BACKEND_MODELS = 318;