/** Hook that fetches the current user's full profile from Supabase
 * (/api/v1/auth/supabase/me) on mount and pushes it into AuthContext.
 * Falls back gracefully when the token is stale or the endpoint is down. */

import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getApiBase } from '../lib/api';

export function useSyncProfile() {
  const { token, user, updateUser, logout } = useAuth();

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    (async () => {
      try {
        const resp = await fetch(
          `${getApiBase()}/api/v1/auth/supabase/me?access_token=${encodeURIComponent(token)}`,
        );
        if (cancelled) return;
        if (resp.status === 401) {
          // stale/expired token — clear it so the user can log in again
          logout();
          return;
        }
        if (!resp.ok) return;
        const data = await resp.json();
        if (data.status !== 'ok') {
          if (data.http === 401) logout();
          return;
        }
        if (cancelled) return;

        const merged = {
          ...(user ?? {}),
          id: data.user_id,
          email: data.email,
          full_name: data.full_name,
          role: data.role,
          language: data.language,
          phone: data.phone,
          country: data.country,
          city: data.city,
          address: data.address,
          birth_year: data.birth_year,
        };
        updateUser(merged);
      } catch (error) {
        console.error('[useSyncProfile] fetch failed', error);
      }
    })();

    return () => {
      cancelled = true;
    };
    // We intentionally only re-run when the token changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);
}