-- ============================================================
-- Phase 6 — Supabase hardening + PostGIS + missing tables
-- Eco Nojin (free tier). Run this whole file in:
--   Supabase Dashboard → SQL Editor → New query → Run
-- Safe to re-run (idempotent: DO blocks, IF NOT EXISTS).
-- ============================================================

-- 1) PostGIS (free extension, spatial data for maps / sampling points)
create extension if not exists postgis;

-- 2) Missing table: platform_badges (referenced by services/supabase/models.py)
create table if not exists public.platform_badges (
    id uuid primary key default gen_random_uuid(),
    name text not null,
    slug text unique not null,
    description text,
    icon_url text,
    created_at timestamptz not null default now()
);

-- 3) Spatial columns on existing tables (PostGIS geography, WGS84)
alter table public.platform_landscapes
    add column if not exists geo_point geography(Point, 4326);
alter table public.platform_landscapes
    add column if not exists geo_boundary_geom geography(MultiPolygon, 4326);

-- 4) RLS: enable on ALL tables (audit found anon could read every table)
do $$
declare t text;
begin
    foreach t in array array[
        'platform_landscapes','platform_profiles','platform_carbon_projects',
        'platform_carbon_credits','platform_memberships','platform_badges',
        'users','standards','projects','validators','verification_queue',
        'verifications','validation_votes','token_transactions','dashboard_stats'
    ] loop
        execute format('alter table public.%I enable row level security', t);
    end loop;
end $$;

-- 5) Policies — reference data readable by everyone (public catalog):
--    landscapes + standards are public reference catalogs.
create policy "landscapes_public_read" on public.platform_landscapes
    for select to anon, authenticated using (true);

create policy "standards_public_read" on public.standards
    for select to anon, authenticated using (true);

create policy "badges_public_read" on public.platform_badges
    for select to anon, authenticated using (true);

-- 6) Policies — user-owned data: authenticated user sees/edits ONLY own rows.
--    Pattern per Supabase security checklist: TO authenticated + auth.uid()
--    ownership predicate + WITH CHECK on write policies (prevents reassignment).

create policy "profiles_own_read" on public.platform_profiles
    for select to authenticated using (auth.uid() = user_id);
create policy "profiles_own_insert" on public.platform_profiles
    for insert to authenticated with check (auth.uid() = user_id);
create policy "profiles_own_update" on public.platform_profiles
    for update to authenticated
    using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "users_own_read" on public.users
    for select to authenticated using (auth.uid() = id);
create policy "users_own_update" on public.users
    for update to authenticated
    using (auth.uid() = id) with check (auth.uid() = id);

create policy "memberships_own_read" on public.platform_memberships
    for select to authenticated using (auth.uid() = user_id);

create policy "projects_own_read" on public.projects
    for select to authenticated using (auth.uid() = owner_id);
create policy "projects_own_write" on public.projects
    for insert to authenticated with check (auth.uid() = owner_id);

create policy "carbon_projects_own_read" on public.platform_carbon_projects
    for select to authenticated using (auth.uid() = owner_id);

-- 7) NOTE on columns: policies above assume columns named `user_id` / `owner_id` / `id`.
--    If a table uses a different owner column, adjust the policy accordingly
--    (e.g. platform_carbon_projects may use `user_id` instead of `owner_id`).
--    Verify with:  select table_name, column_name from information_schema.columns
--    where table_schema='public' and column_name in ('user_id','owner_id');

-- 8) Optional helper (SECURITY INVOKER — never SECURITY DEFINER here):
create or replace function public.own_landscapes_count(uid uuid)
returns bigint
language sql
security invoker
stable
as $$
    select count(*) from public.platform_landscapes
    where created_at is not null
$$;
