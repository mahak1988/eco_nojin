/**
 * React Query hooks for the manual `endpoints/*` API surface.
 *
 * These wrap the typed clients in {@link ../endpoints} with sensible defaults
 * (staleTime, retry, refetchInterval) so feature code stays declarative.
 */

import { useMutation, useQuery, type UseMutationResult, type UseQueryOptions, type UseQueryResult } from '@tanstack/react-query';
import { dashboardApi } from './endpoints/dashboard';
import { carbonApi, type CarbonCalculateRequest, type CarbonCalculateResponse, type CarbonProject } from './endpoints/carbon';
import { modelsApi, motorsApi, type Model, type MotorRunRequest, type MotorRunResponse } from './endpoints/models';
import { satelliteApi } from './endpoints/satellite';
import { soilApi } from './endpoints/soil';
import { climateApi } from './endpoints/climate';

// ===== Dashboard =========================================================

export function useDashboardOverview(
  options?: Omit<UseQueryOptions<Awaited<ReturnType<typeof dashboardApi.getOverview>>>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: ['dashboard', 'overview'],
    queryFn: dashboardApi.getOverview,
    staleTime: 5 * 60_000,
    ...options,
  });
}

export function useDashboardFull(
  options?: Omit<UseQueryOptions<Awaited<ReturnType<typeof dashboardApi.getFullDashboard>>>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: ['dashboard', 'full'],
    queryFn: dashboardApi.getFullDashboard,
    staleTime: 2 * 60_000,
    refetchInterval: 5 * 60_000,
    ...options,
  });
}

export function useDashboardProjects(
  options?: Omit<UseQueryOptions<Awaited<ReturnType<typeof dashboardApi.getProjects>>>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: ['dashboard', 'projects'],
    queryFn: dashboardApi.getProjects,
    staleTime: 60_000,
    ...options,
  });
}

export function useDashboardWeather(
  options?: Omit<UseQueryOptions<Awaited<ReturnType<typeof dashboardApi.getWeather>>>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: ['dashboard', 'weather'],
    queryFn: dashboardApi.getWeather,
    staleTime: 10 * 60_000,
    ...options,
  });
}

export function useDashboardSatellite(
  options?: Omit<UseQueryOptions<Awaited<ReturnType<typeof dashboardApi.getSatellite>>>, 'queryKey' | 'queryFn'>,
) {
  return useQuery({
    queryKey: ['dashboard', 'satellite'],
    queryFn: dashboardApi.getSatellite,
    staleTime: 10 * 60_000,
    ...options,
  });
}

// ===== Carbon ============================================================

export function useCarbonProjects(
  options?: Omit<UseQueryOptions<CarbonProject[]>, 'queryKey' | 'queryFn'>,
): UseQueryResult<CarbonProject[]> {
  return useQuery({
    queryKey: ['carbon', 'projects'],
    queryFn: carbonApi.getProjects,
    staleTime: 60_000,
    ...options,
  });
}

export function useCarbonCalculate(
  options?: Omit<UseMutationOptions<CarbonCalculateResponse, Error, CarbonCalculateRequest>, 'mutationFn'>,
): UseMutationResult<CarbonCalculateResponse, Error, CarbonCalculateRequest> {
  return useMutation({
    mutationFn: carbonApi.calculate,
    ...options,
  });
}

import type { UseMutationOptions } from '@tanstack/react-query';
export type { UseMutationOptions } from '@tanstack/react-query';

// ===== Models / Motors ===================================================

export function useModels(
  options?: Omit<UseQueryOptions<Model[]>, 'queryKey' | 'queryFn'>,
): UseQueryResult<Model[]> {
  return useQuery({
    queryKey: ['models'],
    queryFn: modelsApi.getAll,
    staleTime: 5 * 60_000,
    ...options,
  });
}

export function useRunModel(
  options?: Omit<UseMutationOptions<Awaited<ReturnType<typeof modelsApi.runModel>>, Error, { slug: string; inputs: Record<string, unknown> }>, 'mutationFn'>,
): UseMutationResult<Awaited<ReturnType<typeof modelsApi.runModel>>, Error, { slug: string; inputs: Record<string, unknown> }> {
  return useMutation({
    mutationFn: ({ slug, inputs }) => modelsApi.runModel(slug, inputs),
    ...options,
  });
}

export function useRunMotor(
  options?: Omit<UseMutationOptions<MotorRunResponse, Error, MotorRunRequest>, 'mutationFn'>,
): UseMutationResult<MotorRunResponse, Error, MotorRunRequest> {
  return useMutation({
    mutationFn: motorsApi.run,
    ...options,
  });
}

// ===== Satellite ========================================================

export function useSatelliteHistory(farmId: string) {
  return useQuery({
    queryKey: ['satellite', 'history', farmId],
    queryFn: () => satelliteApi.getHistory(farmId),
    enabled: !!farmId,
    staleTime: 60_000,
  });
}

export function useSatelliteStats(farmId: string) {
  return useQuery({
    queryKey: ['satellite', 'stats', farmId],
    queryFn: () => satelliteApi.getStats(farmId),
    enabled: !!farmId,
    staleTime: 60_000,
  });
}

// ===== Soil =============================================================

export function useSoilHistory(farmId: string) {
  return useQuery({
    queryKey: ['soil', 'history', farmId],
    queryFn: () => soilApi.getHistory(farmId),
    enabled: !!farmId,
    staleTime: 60_000,
  });
}

// ===== Climate ==========================================================

export function useAnalyzeDrought() {
  return useMutation({
    mutationFn: (params: Record<string, unknown>) => climateApi.analyzeDrought(params),
  });
}