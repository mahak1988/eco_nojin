import type { NextRequest } from 'next/server';
import { type GlobalRole, hasRole } from '@/lib/auth/roles';
import { currentUser } from '@/lib/bff/auth-service';
import { BffError } from '@/lib/bff/backend';
import { readSession } from '@/lib/session/session-cookie';

export async function requireRole(request: NextRequest, allowed: readonly GlobalRole[]) {
  const session = await readSession(request);
  if (!session) throw new BffError(401, 'Authentication required');
  const user = await currentUser(session);
  if (!hasRole(user.role, allowed)) {
    throw new BffError(403, 'Insufficient role');
  }
  return { session, user };
}
