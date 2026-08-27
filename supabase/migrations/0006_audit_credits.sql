-- ============================================================
-- Phase 7 — carbon audit + credit issuance (SECURITY DEFINER
-- helpers with explicit role checks inside; role lives on
-- platform_profiles.role). Idempotent.
-- ============================================================

-- 1) Auditor votes on a verification (validator_id = auth.uid())
create or replace function public.auditor_vote(verification_id uuid, vote text, confidence int default 70, comment text default null)
returns boolean
language plpgsql
security definer
set search_path = public
as $$
declare ok boolean;
begin
  select exists(
    select 1 from public.platform_profiles
    where id = auth.uid() and role in ('admin', 'auditor')
  ) into ok;
  if not ok then
    raise exception 'not_authorized';
  end if;
  if vote not in ('approved', 'rejected') then
    raise exception 'invalid_vote';
  end if;
  insert into public.validation_votes (verification_id, validator_id, vote, confidence, comment)
  values (verification_id, auth.uid(), vote, confidence, comment)
  on conflict do nothing;
  return found;
end;
$$;
revoke all on function public.auditor_vote(uuid, text, int, text) from public;
grant execute on function public.auditor_vote(uuid, text, int, text) to authenticated;

-- 2) Admin issues carbon credits for a project
drop function if exists public.admin_issue_credits(uuid, numeric);
create function public.admin_issue_credits(p_project_id uuid, p_amount numeric)
returns table(out_credit_id uuid, out_project_name text, out_credits_issued numeric)
language plpgsql
security definer
set search_path = public
as $$
declare ok boolean;
        pid uuid;
        pname text;
        cur numeric;
begin
  select exists(
    select 1 from public.platform_profiles
    where id = auth.uid() and role = 'admin'
  ) into ok;
  if not ok then
    raise exception 'not_admin';
  end if;
  insert into public.platform_carbon_credits (project_id, owner_id, amount, issued_at)
  select pc.id, pc.owner_id, p_amount, now()
  from public.platform_carbon_projects pc
  where pc.id = p_project_id
  returning id into pid;
  if pid is null then
    raise exception 'project_not_found';
  end if;
  update public.platform_carbon_projects
  set credits_issued = credits_issued + p_amount, status = 'verified', updated_at = now()
  where id = p_project_id
  returning name, credits_issued into pname, cur;
  insert into public.token_transactions
    (user_id, transaction_type, token_type, amount, description, reference_id, reference_type, status)
  select pc.owner_id, 'reward', 'CCT', p_amount,
         'issue of carbon credits for project ' || pname, p_project_id, 'project', 'completed'
  from public.platform_carbon_projects pc
  where pc.id = p_project_id;
  return query select pid, pname, cur;
end;
$$;
revoke all on function public.admin_issue_credits(uuid, numeric) from public;
grant execute on function public.admin_issue_credits(uuid, numeric) to authenticated;
