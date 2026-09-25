import { NextResponse } from 'next/server';
import { getApiProxyTarget } from '@/lib/config/server-env';

export const dynamic = 'force-dynamic';

export async function GET(): Promise<NextResponse> {
  try {
    const response = await fetch(`${getApiProxyTarget()}/api/v1/platform/health`, {
      cache: 'no-store',
      signal: AbortSignal.timeout(2_000),
    });
    if (!response.ok) throw new Error('Backend health check failed');
    return NextResponse.json({ status: 'ready', service: 'eco-nojin-frontend' });
  } catch {
    return NextResponse.json({ status: 'not-ready' }, { status: 503 });
  }
}
