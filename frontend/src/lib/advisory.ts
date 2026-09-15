import { useQuery } from '@tanstack/react-query';
import { getApiBase } from './api';

export interface AdviceEvidence {
  source: string;
  type: string;
  content: string;
  rank?: number;
  category?: string;
}

export interface AdviceResult {
  status: 'ok' | 'error';
  answer?: string;
  error?: string;
  provider?: string;
  evidence?: AdviceEvidence[];
  matched_topics?: string[];
  metrics?: Record<string, number>;
}

export interface AdviceRequest {
  question: string;
  lat?: number;
  lon?: number;
}

export async function fetchAdvice(req: AdviceRequest): Promise<AdviceResult> {
  const response = await fetch(`${getApiBase()}/api/v1/ai/advise`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!response.ok) {
    throw new Error(`advisory_fetch_failed_${response.status}`);
  }
  return (await response.json()) as AdviceResult;
}

export function useAdvisory(question: string, lat?: number, lon?: number) {
  return useQuery<AdviceResult, Error>({
    queryKey: ['advisory', question, lat, lon],
    queryFn: () => fetchAdvice({ question, lat, lon }),
    enabled: question.trim().length >= 3,
    staleTime: 5 * 60 * 1000,
  });
}
