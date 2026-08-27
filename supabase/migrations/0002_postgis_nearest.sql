-- ============================================================
-- Phase 6C — real PostGIS nearest-landscapes (executed 2026-08-27)
-- Eco Nojin (free tier). Idempotent. Requires migration 0001 (PostGIS).
-- ============================================================

-- 1) Backfill geo_point (geography, WGS84) from GeoJSON Point coordinates
update public.platform_landscapes
set geo_point = ST_SetSRID(
        ST_MakePoint(
            (geo_boundary->'coordinates'->>0)::float8,
            (geo_boundary->'coordinates'->>1)::float8
        ), 4326
    )::geography
where geo_boundary->>'type' = 'Point' and geo_point is null;

-- 2) RPC for PostgREST: nearest landscapes via <-> operator on geography
--    (SECURITY INVOKER — never SECURITY DEFINER)
create or replace function public.nearest_landscapes(lat float8, lon float8, lim int default 5)
returns table(id uuid, name text, province text, distance_km float8)
language sql security invoker stable
as $$
  select l.id, l.name, l.province,
         round((ST_Distance(l.geo_point, ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography) / 1000.0)::numeric, 2) as distance_km
  from public.platform_landscapes l
  where l.geo_point is not null
  order by l.geo_point <-> ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography
  limit lim
$$;

-- Verify:  select count(*) from platform_landscapes where geo_point is not null;  -- expect 20
-- Call:   POST /rest/v1/rpc/nearest_landscapes  {"lat":35.7,"lon":51.4,"lim":3}
