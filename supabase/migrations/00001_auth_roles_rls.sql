-- ============================================================================
-- Eco Nojin (اکو نوژین) — Supabase: auth roles + RLS (Phase 0)
-- Roles mirror the app RBAC: farmer, cooperative, NGO, admin
-- Apply with: supabase db push  (or paste in Supabase SQL editor)
-- ============================================================================

-- Helper: current user role from app_metadata (set at signup)
create or replace function public.current_role()
returns text
language sql stable
as $$
  select coalesce(
    nullif(auth.jwt() -> 'app_metadata' ->> 'role', ''),
    'farmer'
  );
$$;

-- Helper: is the caller an admin?
create or replace function public.is_admin()
returns boolean
language sql stable
as $$
  select public.current_role() = 'admin';
$$;

-- ---------------------------------------------------------------------------
-- Core tables are managed by the FastAPI/SQLAlchemy backend (source of truth).
-- These policies protect them when accessed via Supabase:
--  - reads: authenticated users can read their own rows / public catalog rows
--  - writes: admin or owner only
-- ---------------------------------------------------------------------------

-- users profile view (map auth.users -> app users table later)
create or replace view public.user_profiles as
  select id, email, raw_user_meta_data ->> 'full_name' as full_name,
         raw_user_meta_data ->> 'role' as role
  from auth.users;

-- RLS on public.farms (example; repeat the same pattern per table)
alter table public.farms enable row level security;

drop policy if exists "farms_select_own" on public.farms;
create policy "farms_select_own" on public.farms
  for select using (auth.uid() = user_id or public.is_admin());

drop policy if exists "farms_insert_own" on public.farms;
create policy "farms_insert_own" on public.farms
  for insert with check (auth.uid() = user_id);

drop policy if exists "farms_update_own" on public.farms;
create policy "farms_update_own" on public.farms
  for update using (auth.uid() = user_id or public.is_admin());

-- storage buckets for content media (content panel)
insert into storage.buckets (id, name, public)
values ('media', 'media', true)
on conflict (id) do nothing;