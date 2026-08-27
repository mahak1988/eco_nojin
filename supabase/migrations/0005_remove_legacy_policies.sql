-- ============================================================
-- Phase 6C — remove legacy open "Enable all" policies (security fix)
-- These pre-existing policies granted unrestricted ALL access
-- (some to anon) and overrode role-based RLS. Replaced by the
-- explicit policies from 0001/0004. Idempotent.
-- ============================================================

drop policy if exists "Enable all for users" on public.users;
drop policy if exists "Enable all for projects" on public.projects;
drop policy if exists "Enable all for standards" on public.standards;
drop policy if exists "Enable all for verifications" on public.verifications;

-- sanity: standards remains publicly readable via standards_public_read (0001)
