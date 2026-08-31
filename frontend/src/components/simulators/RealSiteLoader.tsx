import { useEffect, useState } from 'react';
import { fetchManualSites, fetchDemGrid, buildRealTerrain } from '../../lib/demApi';
import type { TerrainData } from '../../lib/terrainGenerator';
import { Loader2, Mountain, CheckCircle, AlertCircle } from 'lucide-react';

export interface RealSiteMeta {
  siteId: string;
  lat: number;
  lon: number;
  source: string;
  cached: boolean;
  spanM: number;
  reliefM: number;
}

/**
 * Real-site loader: picks one of the 300 manual-dataset sites and rebuilds
 * the 3D terrain from the REAL Copernicus DEM (cached on the backend).
 */
export default function RealSiteLoader({
  onLoaded,
}: {
  onLoaded: (terrain: TerrainData, meta: RealSiteMeta) => void;
}) {
  const [sites, setSites] = useState<any[]>([]);
  const [siteId, setSiteId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastMeta, setLastMeta] = useState<RealSiteMeta | null>(null);

  useEffect(() => {
    fetchManualSites()
      .then((list) => {
        setSites(list);
        // default: the site with the biggest elevation (best demo terrain)
        const best = [...list].sort((a, b) => (b.elevation_m || 0) - (a.elevation_m || 0))[0];
        if (best) setSiteId(best.site_id);
      })
      .catch(() => setError('فهرست سایت‌ها دریافت نشد'));
  }, []);

  const load = async () => {
    if (!siteId) return;
    setLoading(true);
    setError('');
    try {
      const dem = await fetchDemGrid(siteId);
      const terrain = buildRealTerrain(dem);
      const meta: RealSiteMeta = {
        siteId: dem.site_id,
        lat: dem.lat,
        lon: dem.lon,
        source: dem.source,
        cached: dem.cached,
        spanM: dem.span_m,
        reliefM: dem.max_elev - dem.min_elev,
      };
      setLastMeta(meta);
      onLoaded(terrain, meta);
    } catch (e: any) {
      setError(e?.message || 'خطا در دریافت DEM');
    } finally {
      setLoading(false);
    }
  };

  const card = 'rgba(15, 23, 42, 0.9)';

  return (
    <div
      style={{
        background: card,
        backdropFilter: 'blur(10px)',
        borderRadius: '12px',
        padding: '12px',
        border: '1px solid rgba(255,255,255,0.1)',
      }}
    >
      <div
        style={{
          fontSize: '12px',
          color: 'rgba(255,255,255,0.6)',
          marginBottom: '8px',
          fontWeight: 700,
          textTransform: 'uppercase',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <Mountain size={13} color="#4CAF50" />
        زمین واقعی (DEM)
      </div>

      <select
        value={siteId}
        onChange={(e) => setSiteId(e.target.value)}
        style={{
          width: '100%',
          padding: '8px',
          borderRadius: '8px',
          marginBottom: '8px',
          border: '1px solid rgba(255,255,255,0.15)',
          background: 'rgba(255,255,255,0.06)',
          color: 'white',
          fontSize: '12px',
        }}
      >
        {sites.map((s) => (
          <option key={s.site_id} value={s.site_id} style={{ background: '#16181f' }}>
            {s.site_id} — {s.admin1_city || s.province || s.country} (
            {(s.elevation_m ?? 0).toFixed(0)}m)
          </option>
        ))}
      </select>

      <button
        onClick={() => void load()}
        disabled={loading || !siteId}
        style={{
          width: '100%',
          padding: '9px',
          borderRadius: '8px',
          border: 'none',
          background: 'linear-gradient(135deg, #4CAF50, #2E7D32)',
          color: 'white',
          fontWeight: 700,
          fontSize: '12px',
          cursor: loading ? 'default' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '6px',
          opacity: loading || !siteId ? 0.6 : 1,
        }}
      >
        {loading ? <Loader2 size={14} className="spin" /> : <Mountain size={14} />}
        {loading ? 'دریافت DEM واقعی…' : 'بارگذاری زمین واقعی'}
      </button>

      {lastMeta && (
        <div
          style={{
            marginTop: '8px',
            fontSize: '11px',
            color: '#81C784',
            display: 'flex',
            gap: '6px',
            alignItems: 'center',
          }}
        >
          <CheckCircle size={12} />
          زمین واقعی: {lastMeta.reliefM.toFixed(0)}m ناهمواری / {lastMeta.spanM}m
          {lastMeta.cached ? ' (کش)' : ''}
        </div>
      )}
      {error && (
        <div
          style={{
            marginTop: '8px',
            fontSize: '11px',
            color: '#fca5a5',
            display: 'flex',
            gap: '6px',
            alignItems: 'center',
          }}
        >
          <AlertCircle size={12} /> {error}
        </div>
      )}
    </div>
  );
}
