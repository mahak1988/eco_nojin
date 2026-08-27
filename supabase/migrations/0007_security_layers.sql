-- ============================================================================
-- Migration 0007 — Phase 8-C: security layer + open-data policy
--   * geo_points: public select (OGC API Features open data)
--   * security_events: WAF/rate/anomaly/honeypot events (server-side writes)
--   * audit_log: zero-trust RBAC audit trail
--   * blocked_ips: circuit-breaker / honeypot auto-blocks
-- All statements idempotent.
-- ============================================================================

-- --- 1) platform_landscapes public read (OGC standard open data) ------------
do $$
begin
  if not exists (
    select 1 from pg_policies where tablename = 'platform_landscapes' and policyname = 'landscapes_public_select'
  ) then
    alter table public.platform_landscapes enable row level security;
    create policy landscapes_public_select on public.platform_landscapes
      for select using (true);
  end if;
end $$;

-- OGC-friendly view: id, name, lon, lat from the PostGIS point
create or replace view public.ogc_landscape_points
with (security_invoker = on) as
select id::text as id, name, st_x(geo_point::geometry) as lon, st_y(geo_point::geometry) as lat
from public.platform_landscapes
where geo_point is not null;

-- --- 2) security_events ------------------------------------------------------
create table if not exists public.security_events (
  id uuid primary key default gen_random_uuid(),
  ts timestamptz not null default now(),
  ip text,
  actor text,
  action text,
  decision text,
  severity text default 'info',
  detail jsonb
);

alter table public.security_events enable row level security;

do $$
begin
  if exists (select 1 from pg_policies where tablename = 'security_events' and policyname = 'security_events_own_select') then
    drop policy security_events_own_select on public.security_events;
  end if;
  create policy security_events_own_select on public.security_events
    for select using (actor = auth.uid()::text);
end $$;

do $$
begin
  if exists (select 1 from pg_policies where tablename = 'security_events' and policyname = 'security_events_admin_all') then
    drop policy security_events_admin_all on public.security_events;
  end if;
  create policy security_events_admin_all on public.security_events
    for all using (public.is_admin()) with check (public.is_admin());
end $$;

-- --- 3) audit_log ------------------------------------------------------------
create table if not exists public.audit_log (
  id uuid primary key default gen_random_uuid(),
  ts timestamptz not null default now(),
  actor_id uuid references auth.users(id),
  actor_email text,
  action text not null,
  resource text,
  detail jsonb
);

alter table public.audit_log enable row level security;

do $$
begin
  if exists (select 1 from pg_policies where tablename = 'audit_log' and policyname = 'audit_log_own_select') then
    drop policy audit_log_own_select on public.audit_log;
  end if;
  create policy audit_log_own_select on public.audit_log
    for select using (actor_id = auth.uid());
end $$;

do $$
begin
  if exists (select 1 from pg_policies where tablename = 'audit_log' and policyname = 'audit_log_admin_all') then
    drop policy audit_log_admin_all on public.audit_log;
  end if;
  create policy audit_log_admin_all on public.audit_log
    for all using (public.is_admin()) with check (public.is_admin());
end $$;

-- --- 4) blocked_ips ----------------------------------------------------------
create table if not exists public.blocked_ips (
  ip text primary key,
  reason text,
  until timestamptz,
  created_at timestamptz not null default now()
);

alter table public.blocked_ips enable row level security;

do $$
begin
  if exists (select 1 from pg_policies where tablename = 'blocked_ips' and policyname = 'blocked_ips_admin_all') then
    drop policy blocked_ips_admin_all on public.blocked_ips;
  end if;
  create policy blocked_ips_admin_all on public.blocked_ips
    for all using (public.is_admin()) with check (public.is_admin());
end $$;

-- --- grants ------------------------------------------------------------------
grant select on public.platform_landscapes to anon, authenticated;
grant select on public.ogc_landscape_points to anon, authenticated;
grant select on public.security_events to authenticated;
grant select on public.audit_log to authenticated;
grant select on public.blocked_ips to authenticated;
