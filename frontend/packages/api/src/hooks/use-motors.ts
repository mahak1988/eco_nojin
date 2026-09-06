import { type UseMutationOptions, useMutation } from '@tanstack/react-query';
import { getApiClient } from '../client';
import {
  type MotorChainRequest,
  MotorChainResult,
  type MotorRunRequest,
  MotorRunResult,
} from '../schema/motors';
import { queryKeys } from './query-keys';

export function useRunMotor(
  options?: Omit<UseMutationOptions<MotorRunResult, Error, MotorRunRequest>, 'mutationFn'>,
) {
  return useMutation({
    mutationFn: (req) => getApiClient().post('/motors/run', req, MotorRunResult),
    ...options,
  });
}

export function useRunMotorChain(
  options?: Omit<UseMutationOptions<MotorChainResult, Error, MotorChainRequest>, 'mutationFn'>,
) {
  return useMutation({
    mutationFn: (req) => getApiClient().post('/motors/chain', req, MotorChainResult),
    ...options,
  });
}

// Re-export for convenience so consumers don't reach into schema directly
export { queryKeys };