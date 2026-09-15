import { useQuery } from '@tanstack/react-query';
import { useLang } from '../i18n/LanguageContext';

interface MetricData {
  area_ha: number;
  farmers_trained: number;
  co2_sequestered_tco2e: number;
  credits_issued: number;
  [key: string]: number;
}

interface MetricsReturn {
  metrics: {
    area_ha: number;
    farmers_trained: number;
    co2_sequestered_tco2e: number;
    credits_issued: number;
  };
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isLive: boolean;
  refetch: () => void;
}

async function fetchMetrics(): Promise<MetricData> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || '';
  const response = await fetch(`${baseUrl}/api/metrics`, {
    credentials: 'include',
  });
  if (!response.ok) {
    throw new Error(`Metrics fetch failed: ${response.status}`);
  }
  return response.json();
}

/** TanStack Query-powered metrics hook with 30-second polling. */
export function useMetrics(): MetricsReturn {
  const { lang } = useLang();

  const query = useQuery<MetricData, Error>({
    queryKey: ['metrics', lang],
    queryFn: fetchMetrics,
    enabled: !!import.meta.env.VITE_API_BASE_URL,
    refetchInterval: 30_000,
    refetchOnWindowFocus: true,
    staleTime: 20_000,
    retry: 1,
  });

  const metrics = query.data
    ? {
        area_ha: query.data.area_ha ?? 0,
        farmers_trained: query.data.farmers_trained ?? 0,
        co2_sequestered_tco2e: query.data.co2_sequestered_tco2e ?? 0,
        credits_issued: query.data.credits_issued ?? 0,
      }
    : {
        area_ha: 0,
        farmers_trained: 0,
        co2_sequestered_tco2e: 0,
        credits_issued: 0,
      };

  return {
    metrics,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    isLive: query.isFetching && !query.isLoading,
    refetch: query.refetch,
  };
}
