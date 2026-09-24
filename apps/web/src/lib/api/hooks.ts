import { useQuery } from '@tanstack/react-query';
import {
  api,
  type CppStatus,
  type HydromaModels,
  type Landscapes,
  type MarketplaceProducts,
  type MarketplaceStats,
  type PlatformHealth,
  type PlatformStats,
} from './typed-client';

export const usePlatformHealth = () =>
  useQuery<PlatformHealth, Error>({
    queryKey: ['platform', 'health'],
    queryFn: api.platform.health,
  });

export const usePlatformStats = () =>
  useQuery<PlatformStats, Error>({
    queryKey: ['platform', 'stats'],
    queryFn: api.platform.stats,
  });

export const useLandscapes = () =>
  useQuery<Landscapes, Error>({
    queryKey: ['platform', 'landscapes'],
    queryFn: api.platform.landscapes,
  });

export const useHydromaModels = () =>
  useQuery<HydromaModels, Error>({
    queryKey: ['hydroma', 'models'],
    queryFn: api.hydroma.models,
  });

export const useCppStatus = () =>
  useQuery<CppStatus, Error>({
    queryKey: ['models', 'cpp-status'],
    queryFn: api.hydroma.cppStatus,
  });

export const useMarketplaceProducts = () =>
  useQuery<MarketplaceProducts, Error>({
    queryKey: ['marketplace', 'products'],
    queryFn: api.marketplace.products,
  });

export const useMarketplaceStats = () =>
  useQuery<MarketplaceStats, Error>({
    queryKey: ['marketplace', 'stats'],
    queryFn: api.marketplace.stats,
  });
