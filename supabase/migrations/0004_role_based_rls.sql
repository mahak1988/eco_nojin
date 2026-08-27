-- ============================================================
-- Phase 6C — role-based RLS: admin / auditor / farmer
-- Eco Nojin (free tier). Idempotent (drop-if-exists + IF NOT EXISTS).
-- Roles live on platform_profiles.role (added in 0003, default 'farmer').
-- ============================================================

-- 1) Role helpers (SECURITY INVOKER — respect RLS; auth.uid() from JWT)
create or replace function public.is_admin() returns boolean
language sql stable security invoker
as $$
  select exists (
    select 1 from public.platform_profiles
    where id = auth.uid() and role = 'admin'
  );
$$;

create or replace function public.is_auditor() returns boolean
language sql stable security invoker
as $$
  select exists (
    select 1 from public.platform_profiles
    where id = auth.uid() and role in ('admin', 'auditor')
  );
$$;

-- 2) Admin role assignment — SECURITY DEFINER with an explicit admin check
--    INSIDE the function (standard Supabase admin-function pattern; the check
--    uses auth.uid() against platform_profiles.role before any write).
create or replace function public.admin_set_role(target uuid, new_role text)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare ok boolean;
begin
  select exists(
    select 1 from public.platform_profiles where id = auth.uid() and role = 'admin'
  ) into ok;
  if not ok then
    raise exception 'not_admin';
  end if;
  if new_role not in ('farmer', 'auditor', 'admin') then
    raise exception 'invalid_role';
  end if;
  update public.platform_profiles set role = new_role, updated_at = now()
  where id = target;
  return found;
end;
$$;
revoke all on function public.admin_set_role(uuid, text) from public;
grant execute on function public.admin_set_role(uuid, text) to authenticated;

-- 3) users: owner + admin
drop policy if exists "users_own_read" on public.users;
create policy "users_own_read" on public.users
    for select to authenticated using (auth.uid() = id);
drop policy if exists "users_admin_read" on public.users;
create policy "users_admin_read" on public.users
    for select to authenticated using (public.is_admin());

-- 4) projects (owner column: user_id)
drop policy if exists "projects_own_read" on public.projects;
create policy "projects_own_read" on public.projects
    for select to authenticated using (auth.uid() = user_id);
drop policy if exists "projects_own_insert" on public.projects;
create policy "projects_own_insert" on public.projects
    for insert to authenticated with check (auth.uid() = user_id);
drop policy if exists "projects_admin_read" on public.projects;
create policy "projects_admin_read" on public.projects
    for select to authenticated using (public.is_admin());

-- 5) platform_memberships: owner (existing) + admin read-all
drop policy if exists "memberships_own_read" on public.platform_memberships;
create policy "memberships_own_read" on public.platform_memberships
    for select to authenticated using (auth.uid() = user_id);
drop policy if exists "memberships_admin_read" on public.platform_memberships;
create policy "memberships_admin_read" on public.platform_memberships
    for select to authenticated using (public.is_admin());

-- 6) dashboard_stats is a VIEW -> enforce base-table RLS (security_invoker)
alter view public.dashboard_stats set (security_invoker = on);

-- 7) token_transactions: owner + admin
drop policy if exists "tx_own_read" on public.token_transactions;
create policy "tx_own_read" on public.token_transactions
    for select to authenticated using (auth.uid() = user_id);
drop policy if exists "tx_admin_read" on public.token_transactions;
create policy "tx_admin_read" on public.token_transactions
    for select to authenticated using (public.is_admin());

-- 8) validators: admin-only
drop policy if exists "validators_admin_all" on public.validators;
create policy "validators_admin_all" on public.validators
    for select to authenticated using (public.is_admin());
drop policy if exists "validators_admin_insert" on public.validators;
create policy "validators_admin_insert" on public.validators
    for insert to authenticated with check (public.is_admin());
drop policy if exists "validators_admin_update" on public.validators;
create policy "validators_admin_update" on public.validators
    for update to authenticated using (public.is_admin()) with check (public.is_admin());

-- 9) validation_votes: own + auditor/admin
drop policy if exists "votes_own_read" on public.validation_votes;
create policy "votes_own_read" on public.validation_votes
    for select to authenticated using (auth.uid() = validator_id);
drop policy if exists "votes_staff_read" on public.validation_votes;
create policy "votes_staff_read" on public.validation_votes
    for select to authenticated using (public.is_admin() or public.is_auditor());
drop policy if exists "votes_staff_insert" on public.validation_votes;
create policy "votes_staff_insert" on public.validation_votes
    for insert to authenticated
    with check (public.is_admin() or public.is_auditor());

-- 10) verifications: auditor/admin read (owner column unknown -> staff-only)
drop policy if exists "verifications_staff_read" on public.verifications;
create policy "verifications_staff_read" on public.verifications
    for select to authenticated using (public.is_admin() or public.is_auditor());

-- 11) verification_queue is a VIEW -> enforce base-table RLS (PG15 security_invoker)
alter view public.verification_queue set (security_invoker = on);

-- 12) platform_carbon_projects: admin read-all (owner policies already exist)
drop policy if exists "carbon_projects_admin_read" on public.platform_carbon_projects;
create policy "carbon_projects_admin_read" on public.platform_carbon_projects
    for select to authenticated using (public.is_admin());
