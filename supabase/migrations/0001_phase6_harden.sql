-- ============================================================
-- Phase 6 — Supabase hardening + PostGIS + missing tables
-- Eco Nojin (free tier). Run this whole file in:
--   Supabase Dashboard → SQL Editor → New query → Run
-- Safe to re-run (idempotent: DO blocks, IF NOT EXISTS).
--
-- FIXED (2026-08-27): policies now match the REAL schema
-- (services/supabase/migrations/001_platform_tables.sql):
--   platform_profiles.id REFERENCES auth.users(id)  ->  auth.uid() = id
--   platform_memberships.user_id / carbon_projects.owner_id stay as-is.
--   users / projects / validators / verification_* / token_transactions
--   get RLS ENABLED ONLY (deny-all default) until their schema is known.
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

-- 4) RLS: enable on ALL exposed tables (audit found anon could read everything)
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
create policy "landscapes_public_read" on public.platform_landscapes
    for select to anon, authenticated using (true);

create policy "standards_public_read" on public.standards
    for select to anon, authenticated using (true);

create policy "badges_public_read" on public.platform_badges
    for select to anon, authenticated using (true);

-- 6) Policies — user-owned data (REAL schema: profiles.id = auth.users.id):
create policy "profiles_own_read" on public.platform_profiles
    for select to authenticated using (auth.uid() = id);
create policy "profiles_own_insert" on public.platform_profiles
    for insert to authenticated with check (auth.uid() = id);
create policy "profiles_own_update" on public.platform_profiles
    for update to authenticated
    using (auth.uid() = id) with check (auth.uid() = id);

create policy "memberships_own_read" on public.platform_memberships
    for select to authenticated using (auth.uid() = user_id);

create policy "carbon_projects_own_read" on public.platform_carbon_projects
    for select to authenticated using (auth.uid() = owner_id);
create policy "carbon_projects_own_insert" on public.platform_carbon_projects
    for insert to authenticated with check (auth.uid() = owner_id);
create policy "carbon_projects_own_update" on public.platform_carbon_projects
    for update to authenticated
    using (auth.uid() = owner_id) with check (auth.uid() = owner_id);

-- 7) NOTE on RLS-only tables (users, projects, validators, verification_*,
--    token_transactions, dashboard_stats, validation_votes):
--    RLS is now ON with NO policies -> deny-all (safest default). Once their
--    schemas are known, add policies explicitly. Service-role calls bypass RLS,
--    so internal admin flows keep working.

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
