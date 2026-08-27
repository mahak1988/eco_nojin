-- ============================================================
-- Phase 6C — cloud LMS (courses / lessons / progress) + RLS
-- Eco Nojin (free tier). Idempotent. Requires migration 0001.
-- ============================================================

-- 1) Courses (public catalog)
create table if not exists public.lms_courses (
    id uuid primary key default gen_random_uuid(),
    slug text unique not null,
    title text not null,
    level text,
    duration_min int default 0,
    description text,
    lesson_count int default 0,
    created_at timestamptz not null default now()
);

-- 2) Lessons (public catalog)
create table if not exists public.lms_lessons (
    id uuid primary key default gen_random_uuid(),
    course_id uuid references public.lms_courses(id) on delete cascade,
    position int default 0,
    title text not null,
    minutes int default 0,
    content text
);

-- 3) Progress (owner-only: one row per user+lesson)
create table if not exists public.lms_progress (
    user_id uuid references auth.users(id) on delete cascade,
    lesson_id uuid references public.lms_lessons(id) on delete cascade,
    completed_at timestamptz not null default now(),
    primary key (user_id, lesson_id)
);

-- 4) RLS
alter table public.lms_courses enable row level security;
alter table public.lms_lessons enable row level security;
alter table public.lms_progress enable row level security;

drop policy if exists "lms_courses_public_read" on public.lms_courses;
create policy "lms_courses_public_read" on public.lms_courses
    for select to anon, authenticated using (true);
drop policy if exists "lms_lessons_public_read" on public.lms_lessons;
create policy "lms_lessons_public_read" on public.lms_lessons
    for select to anon, authenticated using (true);

drop policy if exists "lms_progress_own_read" on public.lms_progress;
create policy "lms_progress_own_read" on public.lms_progress
    for select to authenticated using (auth.uid() = user_id);
drop policy if exists "lms_progress_own_insert" on public.lms_progress;
create policy "lms_progress_own_insert" on public.lms_progress
    for insert to authenticated with check (auth.uid() = user_id);
drop policy if exists "lms_progress_own_delete" on public.lms_progress;
create policy "lms_progress_own_delete" on public.lms_progress
    for delete to authenticated using (auth.uid() = user_id);

-- 5) Roles: platform_profiles gets a role column (default 'farmer');
--    role-based policies are added once the admin flow exists.
alter table public.platform_profiles
    add column if not exists role text not null default 'farmer';
