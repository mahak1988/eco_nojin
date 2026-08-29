import { useEffect, useMemo, useState } from 'react';
import { Play, RefreshCw, CheckCircle, XCircle, Cpu } from 'lucide-react';
import './AdminTheme.css';

const API_BASE = 'http://localhost:8000/api/v1';

const MOTOR_LABELS: Record<string, string> = {
  aquacrop: 'AquaCrop — عملکرد محصول (FAO)',
  irrigation: 'برنامه‌ریز آبیاری',
  planting: 'تقویم کاشت',
  crop_advisor: 'مشاور انتخاب محصول',
  rusle: 'فرسایش RUSLE (نیازمند DEM)',
};

interface SiteRow {
  site_id: string;
  country?: string;
  admin1_city?: string;
  province?: string;
  lat?: number;
  lon?: number;
  koppen?: string;
}

export default function MotorRunner() {
  const [sites, setSites] = useState<SiteRow[]>([]);
  const [siteId, setSiteId] = useState('');
  const [motor, setMotor] = useState('aquacrop');
  const [cropName, setCropName] = useState('wheat');
  const [plantingDate, setPlantingDate] = useState('2022-11-05');
  const [simStart, setSimStart] = useState('2022-11-01');
  const [simEnd, setSimEnd] = useState('2023-06-30');
  const [seasonDays, setSeasonDays] = useState(120);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [loadingSites, setLoadingSites] = useState(true);

  const fetchSites = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + '/motors/manual-sites', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSites(data.sites || []);
        if (data.sites?.length) setSiteId(data.sites[0].site_id);
      }
    } finally {
      setLoadingSites(false);
    }
  };

  useEffect(() => {
    fetchSites();
  }, []);

  const run = async () => {
    if (!siteId) return;
    setRunning(true);
    setError('');
    setResult(null);
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + `/motors/site-run/${motor}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          site_id: siteId,
          crop_name: cropName,
          planting_date: plantingDate,
          sim_start: simStart,
          sim_end: simEnd,
          season_days: seasonDays,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
      setResult(data);
    } catch (e: any) {
      setError(e?.message || 'خطای اجرا');
    } finally {
      setRunning(false);
    }
  };

  const site = useMemo(() => sites.find(s => s.site_id === siteId), [sites, siteId]);

  return (
    <div className="admin-page-container">
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <Cpu size={32} style={{ color: 'var(--accent-primary)' }} />
            اجرای موتورهای علمی روی سایت واقعی
          </h1>
          <p className="page-subtitle">
            اجرای یک‌کلیکی AquaCrop / آبیاری / تقویم کاشت / مشاور محصول با داده‌ی دستی تزریق‌شده
          </p>
        </div>
        <button className="refresh-btn" onClick={fetchSites}>
          <RefreshCw size={16} /> بروزرسانی سایت‌ها
        </button>
      </div>

      <div className="chart-container" style={{ padding: '20px', display: 'grid', gap: '14px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
          <label style={{ display: 'grid', gap: '6px', fontSize: '13px' }}>
            سایت (از دیتابیس دستی — {sites.length} سایت)
            <select
              value={siteId}
              onChange={e => setSiteId(e.target.value)}
              disabled={loadingSites}
              style={{
                padding: '10px', borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-hover)', color: 'var(--text-primary)',
              }}
            >
              {sites.map(s => (
                <option key={s.site_id} value={s.site_id}>
                  {s.site_id} — {s.admin1_city || s.province || s.country} ({s.lat?.toFixed(2)}, {s.lon?.toFixed(2)}) {s.koppen || ''}
                </option>
              ))}
            </select>
          </label>

          <label style={{ display: 'grid', gap: '6px', fontSize: '13px' }}>
            موتور
            <select
              value={motor}
              onChange={e => setMotor(e.target.value)}
              style={{
                padding: '10px', borderRadius: '8px',
                border: '1px solid var(--border-color)',
                background: 'var(--bg-hover)', color: 'var(--text-primary)',
              }}
            >
              {Object.entries(MOTOR_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </label>
        </div>

        {site && (
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            پروفایل: {site.country} / {site.admin1_city || site.province} | ارتفاع {site.elevation_m} متر | اقلیم {site.koppen || '—'}
          </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px' }}>
          <label style={{ display: 'grid', gap: '6px', fontSize: '13px' }}>
            نام محصول (FAO)
            <input value={cropName} onChange={e => setCropName(e.target.value)} className="admin-input"
              style={{ padding: '9px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-hover)', color: 'var(--text-primary)' }} />
          </label>
          {motor === 'aquacrop' && (
            <>
              <label style={{ display: 'grid', gap: '6px', fontSize: '13px' }}>
                تاریخ کاشت
                <input type="date" value={plantingDate} onChange={e => setPlantingDate(e.target.value)} className="admin-input"
                  style={{ padding: '9px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-hover)', color: 'var(--text-primary)' }} />
              </label>
              <label style={{ display: 'grid', gap: '6px', fontSize: '13px' }}>
                شروع شبیه‌سازی
                <input type="date" value={simStart} onChange={e => setSimStart(e.target.value)} className="admin-input"
                  style={{ padding: '9px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-hover)', color: 'var(--text-primary)' }} />
              </label>
              <label style={{ display: 'grid', gap: '6px', fontSize: '13px' }}>
                پایان شبیه‌سازی
                <input type="date" value={simEnd} onChange={e => setSimEnd(e.target.value)} className="admin-input"
                  style={{ padding: '9px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-hover)', color: 'var(--text-primary)' }} />
              </label>
            </>
          )}
          {motor === 'irrigation' && (
            <label style={{ display: 'grid', gap: '6px', fontSize: '13px' }}>
              طول فصل (روز)
              <input type="number" value={seasonDays} onChange={e => setSeasonDays(Number(e.target.value))} className="admin-input"
                style={{ padding: '9px', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--bg-hover)', color: 'var(--text-primary)' }} />
            </label>
          )}
        </div>

        <button
          onClick={run}
          disabled={running || !siteId}
          style={{
            justifySelf: 'start',
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '11px 22px', borderRadius: '10px', border: 'none',
            cursor: running ? 'default' : 'pointer',
            background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
            color: '#fff', fontWeight: 600, opacity: running ? 0.6 : 1,
          }}
        >
          <Play size={16} /> {running ? 'در حال اجرا…' : 'اجرای موتور'}
        </button>
      </div>

      {error && (
        <div className="chart-container" style={{ padding: '16px 20px', display: 'flex', gap: '10px', alignItems: 'center' }}>
          <XCircle size={18} style={{ color: 'var(--accent-danger)' }} />
          <span>{error}</span>
        </div>
      )}

      {result && (
        <div className="chart-container" style={{ padding: '20px' }}>
          <div className="chart-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <CheckCircle size={18} style={{ color: 'var(--accent-primary)' }} />
            نتیجه: {MOTOR_LABELS[result.motor] || result.motor} — سایت {result.site?.site_id}
          </div>
          <pre
            dir="ltr"
            style={{
              fontSize: '12px', lineHeight: 1.7, whiteSpace: 'pre-wrap',
              background: 'var(--bg-hover)', padding: '14px', borderRadius: '10px',
              border: '1px solid var(--border-color)', overflowX: 'auto',
            }}
          >
            {JSON.stringify({ summary: result.result?.summary, outputs: result.result?.outputs, provenance: result.provenance }, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
