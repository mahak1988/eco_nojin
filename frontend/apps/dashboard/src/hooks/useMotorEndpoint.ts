import { useMutation, type UseMutationResult } from '@tanstack/react-query';
import { apiClient } from '@eco/api/mutator';

type MotorResponse = Record<string, unknown>;

/**
 * Generic mutation wrapper for any backend POST endpoint that runs a model.
 * Returns the typed result without going through Zod parsing.
 */
export function useRunMotorEndpoint<Response = MotorResponse, Variables = Record<string, unknown>>(
  path: string,
): UseMutationResult<Response, Error, Variables> {
  return useMutation<Response, Error, Variables>({
    mutationFn: async (payload) => {
      const { data } = await apiClient.post<Response>(path, payload);
      return data;
    },
  });
}

export function useGetMotorEndpoint<Response = MotorResponse>(
  path: string,
): UseMutationResult<Response, Error, Record<string, unknown>> {
  return useMutation<Response, Error, Record<string, unknown>>({
    mutationFn: async (payload) => {
      const { data } = await apiClient.get<Response>(path, { params: payload });
      return data;
    },
  });
}