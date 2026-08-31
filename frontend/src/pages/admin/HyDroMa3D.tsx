/**
 * HyDroMa 3D Simulator — isometric digital-twin of the platform
 * Reference style: farm-tycoon isometric + technical GIS digital twin
 * Data: 100% real — manual dataset (sites/weather/soil/crops) + scientific motors
 */
import { ReactNode, useEffect, useMemo, useRef, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { usePipelineSafe } from '../../contexts/SimulationPipeline';
import { OrbitControls, Html } from '@react-three/drei';
import {
  Play,
  Pause,
  FastForward,
  Sun,
  CloudRain,
  Wind,
  Thermometer,
  Sprout,
  Droplets,
  TrendingUp,
  Loader2,
  CheckCircle,
  XCircle,
  Coins,
  Users,
  MapPin,
  Settings,
  Bell,
  HelpCircle,
  Camera,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import './AdminTheme.css';

const API = 'http://localhost:8000/api/v1';

/* ------------------------------------------------------------------ types */
interface SiteRow {
  site_id: string;
  country?: string;
  admin1_city?: string;
  province?: string;
  lat?: number;
  lon?: number;
  elevation_m?: number;
  koppen?: string;
  annual_rain_normal_mm?: number;
}
interface NormalRow {
  month: number;
  tmax_c: number;
  tmin_c: number;
  tavg_c: number;
  precip_mm: number;
  et0_mm: number;
}
interface CropRow {
  species_id: string;
  scientific_name?: string;
  crop_note_fa?: string;
  kc_ini: number;
  kc_mid: number;
  kc_end: number;
  root_depth_m: number;
  base_temp_c?: number;
}
interface MotorResultBundle {
  motor: string;
  site?: Record<string, unknown>;
  provenance?: Record<string, unknown>;
  result?: {
    status: string;
    summary?: Record<string, unknown>;
    outputs?: Record<string, unknown>;
    error_message?: string;
  };
}

/* ------------------------------------------------------------- api client */
const token = () => localStorage.getItem('access_token');
async function api<T = any>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API + path, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token() || ''}`,
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json();
}

/* ------------------------------------------------------- 3D scene helpers */
function cropColorFor(month: number): string {
  // growth cycle coloring: green ramp Mar..Sep, brown-ish off-season
  const ramp = [
    '#6b4c2a',
    '#7a5c30',
    '#8a7a35',
    '#5d8a2f',
    '#4a9a2a',
    '#3fae2a',
    '#35b52f',
    '#2fa829',
    '#5d9a35',
    '#8a8a35',
    '#9a7a3f',
    '#7a5c30',
  ];
  return ramp[(month - 1 + 12) % 12];
}

function FieldPlot({
  position,
  size,
  color,
  selected,
  onClick,
  label,
}: {
  position: [number, number, number];
  size: number;
  color: string;
  selected: boolean;
  onClick: () => void;
  label?: string;
}) {
  return (
    <group position={position} onClick={onClick}>
      <mesh ref={ref} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[size, size]} />
        <meshStandardMaterial color={color} />
      </mesh>
      {selected && (
        <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.02, 0]}>
          <planeGeometry args={[size * 1.06, size * 1.06]} />
          <meshBasicMaterial color="#00FF41" transparent opacity={0.35} />
        </mesh>
      )}
      {selected && label && (
        <Html center position={[0, 1.2, 0]} distanceFactor={14}>
          <div
            style={{
              background: 'rgba(20,25,30,0.92)',
              color: '#fff',
              padding: '6px 12px',
              borderRadius: 8,
              border: '1px solid rgba(255,255,255,0.15)',
              fontSize: 12,
              whiteSpace: 'nowrap',
              fontFamily: 'inherit',
            }}
          >
            {label}
          </div>
        </Html>
      )}
    </group>
  );
}

function Barn({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh castShadow position={[0, 1, 0]}>
        <boxGeometry args={[3.2, 2, 2.4]} />
        <meshStandardMaterial color="#8B5A2B" />
      </mesh>
      <mesh castShadow position={[0, 2.35, 0]} rotation={[0, Math.PI / 4, 0]}>
        <coneGeometry args={[2.4, 1.2, 4]} />
        <meshStandardMaterial color="#2F4F2F" />
      </mesh>
    </group>
  );
}

function Silo({ position, capacity }: { position: [number, number, number]; capacity: string }) {
  return (
    <group position={position}>
      <mesh castShadow position={[0, 1.6, 0]}>
        <cylinderGeometry args={[0.7, 0.7, 3.2, 16]} />
        <meshStandardMaterial color="#A9A9A9" metalness={0.6} roughness={0.35} />
      </mesh>
      <mesh castShadow position={[0, 3.4, 0]}>
        <coneGeometry args={[0.75, 0.6, 16]} />
        <meshStandardMaterial color="#8a8a8a" metalness={0.5} />
      </mesh>
      <Html center position={[0, 2.2, 0.9]} distanceFactor={12}>
        <div
          style={{
            background: 'rgba(20,25,30,0.85)',
            color: '#FFD700',
            padding: '2px 8px',
            borderRadius: 6,
            fontSize: 11,
            fontWeight: 700,
            fontFamily: 'monospace',
          }}
        >
          {capacity}
        </div>
      </Html>
    </group>
  );
}

function Greenhouse({ position }: { position: [number, number, number] }) {
  return (
    <group position={position}>
      <mesh castShadow position={[0, 0.9, 0]}>
        <boxGeometry args={[3.4, 1.8, 2]} />
        <meshStandardMaterial
          color="#87CEEB"
          transparent
          opacity={0.55}
          metalness={0.2}
          roughness={0.1}
        />
      </mesh>
      <mesh position={[0, 1.85, 0]}>
        <boxGeometry args={[3.5, 0.1, 2.1]} />
        <meshStandardMaterial color="#5a8fa8" />
      </mesh>
    </group>
  );
}

function Tree({
  position,
  kind,
}: {
  position: [number, number, number];
  kind: 'deciduous' | 'coniferous';
}) {
  return (
    <group position={position}>
      <mesh castShadow position={[0, 0.5, 0]}>
        <cylinderGeometry args={[0.12, 0.18, 1, 6]} />
        <meshStandardMaterial color="#5D4037" />
      </mesh>
      {kind === 'coniferous' ? (
        <mesh castShadow position={[0, 1.7, 0]}>
          <coneGeometry args={[0.8, 2, 8]} />
          <meshStandardMaterial color="#1E3D1A" />
        </mesh>
      ) : (
        <mesh castShadow position={[0, 1.9, 0]}>
          <sphereGeometry args={[0.85, 12, 10]} />
          <meshStandardMaterial color="#2E7D32" />
        </mesh>
      )}
    </group>
  );
}

function Pond({ position, level }: { position: [number, number, number]; level: number }) {
  return (
    <mesh position={position} rotation={[-Math.PI / 2, 0, 0]}>
      <circleGeometry args={[2.6, 24]} />
      <meshStandardMaterial
        color={level > 0.5 ? '#3b82c4' : '#6b7fa3'}
        transparent
        opacity={0.85}
        metalness={0.3}
        roughness={0.15}
      />
    </mesh>
  );
}

/* ------------------------------------------------------------------ scene */
function Scene({
  month,
  selectedPlot,
  onSelectPlot,
  precipLevel,
}: {
  month: number;
  selectedPlot: number | null;
  onSelectPlot: (i: number | null) => void;
  precipLevel: number;
}) {
  const sunAngle = ((month - 1) / 12) * Math.PI * 2;
  const sunPos: [number, number, number] = [
    Math.cos(sunAngle) * 30,
    22 + Math.sin(sunAngle) * 8,
    Math.sin(sunAngle) * 20 + 10,
  ];
  const crop = cropColorFor(month);
  const gridSize = 6;
  const plotSize = 5.2;

  const plots = useMemo(() => {
    const arr: { i: number; pos: [number, number, number]; kind: string }[] = [];
    let i = 0;
    for (let gx = 0; gx < gridSize; gx++) {
      for (let gz = 0; gz < gridSize; gz++) {
        const isFarm = gx >= 1 && gx <= 3 && gz >= 2 && gz <= 4;
        arr.push({
          i: i++,
          pos: [(gx - (gridSize - 1) / 2) * plotSize, 0, (gz - (gridSize - 1) / 2) * plotSize],
          kind: isFarm ? 'farm' : gx > 3 ? 'orchard' : 'grass',
        });
      }
    }
    return arr;
  }, []);

  const trees: { pos: [number, number, number]; kind: 'deciduous' | 'coniferous' }[] =
    useMemo(() => {
      const t: { pos: [number, number, number]; kind: 'deciduous' | 'coniferous' }[] = [];
      const rng = (seed: number) => (((Math.sin(seed * 12.9898) * 43758.5453) % 1) + 1) % 1;
      for (let s = 0; s < 26; s++) {
        const x = (rng(s * 3.1) - 0.5) * 52;
        const z = (rng(s * 7.7) - 0.5) * 52;
        if (Math.abs(x) < 14 && Math.abs(z) < 14) continue;
        t.push({ pos: [x, 0, z], kind: s % 3 === 0 ? 'coniferous' : 'deciduous' });
      }
      return t;
    }, []);

  return (
    <>
      <color attach="background" args={['#C8E6C9']} />
      <fog attach="fog" args={['#C8E6C9', 60, 160]} />
      <ambientLight intensity={0.55} color="#FFF8E1" />
      <directionalLight
        position={sunPos}
        intensity={1.15}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-40}
        shadow-camera-right={40}
        shadow-camera-top={40}
        shadow-camera-bottom={-40}
      />
      {/* ground */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow position={[0, -0.02, 0]}>
        <planeGeometry args={[110, 110]} />
        <meshStandardMaterial color="#558B2F" />
      </mesh>

      {/* field plots */}
      {plots.map((p) => (
        <FieldPlot
          key={p.i}
          position={p.pos}
          size={plotSize * 0.92}
          color={p.kind === 'farm' ? crop : p.kind === 'orchard' ? '#4a7c23' : '#5d8a3f'}
          selected={selectedPlot === p.i}
          onClick={() => onSelectPlot(selectedPlot === p.i ? null : p.i)}
          label={selectedPlot === p.i ? `پلات ${p.i + 1} • ماه ${month}` : undefined}
        />
      ))}

      {/* crop rows on farm plots */}
      {plots
        .filter((p) => p.kind === 'farm')
        .map((p) => (
          <group key={`rows-${p.i}`} position={[p.pos[0], 0.05, p.pos[2]]}>
            {[-1.6, -0.8, 0, 0.8, 1.6]
              .map((off: any) => (
                <mesh key={off} rotation={[-Math.PI / 2, 0, 0]}>
                  <planeGeometry args={[plotSize * 0.75, 0.22]} />
                  <meshStandardMaterial color="#3e7a1f" transparent opacity={0.55} />
                </mesh>
              ))
              .map((el, idx) => (
                <group key={idx} position={[0, 0, off * 0.85]}>
                  {el}
                </group>
              ))}
          </group>
        ))}

      {/* buildings */}
      <Barn position={[-16, 0, -10]} />
      <Silo position={[-12.5, 0, -11.5]} capacity="50" />
      <Silo position={[-10.5, 0, -12.5]} capacity="30" />
      <Greenhouse position={[13, 0, -9]} />

      {/* trees */}
      {trees.map((t, i) => (
        <Tree key={i} position={t.pos} kind={t.kind} />
      ))}

      {/* pond — level follows real precipitation */}
      <Pond position={[16, 0.01, 12]} level={precipLevel} />

      {/* roads */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, 18]}>
        <planeGeometry args={[70, 2.4]} />
        <meshStandardMaterial color="#9E9E9E" />
      </mesh>
    </>
  );
}

/* ------------------------------------------------------------- HUD pieces */
function Panel({ children, style }: { children: ReactNode; style?: Record<string, unknown> }) {
  return (
    <div
      style={{
        background: 'rgba(20,25,30,0.92)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 12,
        backdropFilter: 'blur(10px)',
        color: '#fff',
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function StatChip({
  icon,
  value,
  color,
}: {
  icon: React.ReactNode;
  value: string;
  color?: string;
}) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 5,
        fontSize: 12,
        fontWeight: 700,
        color: color || '#fff',
      }}
    >
      {icon} {value}
    </div>
  );
}

/* ================================================================ page */
export default function HyDroMa3D() {
  const [sites, setSites] = useState<SiteRow[]>([]);
  const [siteId, setSiteId] = useState('');
  const [normals, setNormals] = useState<NormalRow[]>([]);
  const [crops, setCrops] = useState<CropRow[]>([]);
  const [month, setMonth] = useState(6);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [selectedPlot, setSelectedPlot] = useState<number | null>(null);
  const [running, setRunning] = useState<string | null>(null);
  const [result, setResult] = useState<MotorResultBundle | null>(null);
  const [aiStatus, setAiStatus] = useState<any>(null);
  const pipeline = usePipelineSafe();
  const [panelTab, setPanelTab] = useState<'plant' | 'irrigate' | 'analyze'>('plant');
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  /* data loading */
  useEffect(() => {
    api<{ sites: SiteRow[] }>('/manual/sites')
      .then((d) => {
        setSites(d.sites || []);
        if (d.sites?.length) setSiteId(d.sites[0].site_id);
      })
      .catch(() => {});
    api('/ai/status')
      .then(setAiStatus)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!siteId) return;
    api<{ months: NormalRow[] }>(`/manual/climate-normals/${siteId}`)
      .then((d) => setNormals(d.months || []))
      .catch(() => {});
    api<{ crops: CropRow[] }>('/manual/crop-params')
      .then((d) => setCrops(d.crops || []))
      .catch(() => {});
  }, [siteId]);

  /* season animation */
  useEffect(() => {
    if (timer.current) clearInterval(timer.current);
    if (playing) {
      timer.current = setInterval(() => setMonth((m) => (m % 12) + 1), 1500 / speed);
    }
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [playing, speed]);

  const currentNormal = normals.find((n) => n.month === month) || normals[0];
  const precipLevel = currentNormal ? Math.min(1, (currentNormal.precip_mm || 0) / 80) : 0.5;
  const selectedSite = sites.find((s) => s.site_id === siteId);

  const chartData = normals.map((n) => ({
    month: `${n.month}`,
    et0: n.et0_mm,
    precip: n.precip_mm,
    tavg: n.tavg_c,
  }));

  const runMotor = async (motor: string, extra: Record<string, unknown> = {}) => {
    setRunning(motor);
    setResult(null);
    try {
      const data = await api<MotorResultBundle>(`/motors/site-run/${motor}`, {
        method: 'POST',
        body: JSON.stringify({ site_id: siteId, ...extra }),
      });
      setResult(data);
      if (pipeline?.setApiResult && data.result?.outputs) {
        pipeline.setApiResult(`motor:${motor}`, {
          outputs: data.result.outputs,
          summary: data.result.summary,
          site: data.site,
        });
      }
    } catch (e: any) {
      setResult({ motor, result: { status: 'failed', error_message: e?.message || 'خطا' } });
    } finally {
      setRunning(null);
    }
  };

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: 'calc(100vh - 130px)',
        minHeight: 560,
        borderRadius: 14,
        overflow: 'hidden',
        border: '1px solid var(--border-color)',
      }}
    >
      {/* 3D canvas */}
      <Canvas shadows camera={{ position: [26, 22, 26], fov: 40 }}>
        <Scene
          month={month}
          selectedPlot={selectedPlot}
          onSelectPlot={setSelectedPlot}
          precipLevel={precipLevel}
        />
        <OrbitControls
          maxPolarAngle={Math.PI / 2.15}
          minDistance={15}
          maxDistance={90}
          target={[0, 0, 0]}
        />
      </Canvas>

      {/* top bar: site picker + resource */}
      <div
        style={{
          position: 'absolute',
          top: 12,
          left: 12,
          right: 12,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 12,
        }}
      >
        <Panel style={{ padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 10 }}>
          <MapPin size={16} style={{ color: '#4CAF50' }} />
          <select
            value={siteId}
            onChange={(e) => setSiteId(e.target.value)}
            style={{
              background: 'transparent',
              color: '#fff',
              border: 'none',
              outline: 'none',
              fontSize: 13,
              fontWeight: 600,
              maxWidth: 320,
            }}
          >
            {sites.map((s) => (
              <option key={s.site_id} value={s.site_id} style={{ background: '#16181f' }}>
                {s.site_id} — {s.admin1_city || s.province || s.country} ({s.lat?.toFixed(2)},{' '}
                {s.lon?.toFixed(2)})
              </option>
            ))}
          </select>
          {selectedSite?.koppen && (
            <span style={{ fontSize: 11, color: '#B0BEC5' }}>کوپن {selectedSite.koppen}</span>
          )}
        </Panel>

        <Panel style={{ padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
          <Sprout size={18} style={{ color: '#4CAF50' }} />
          <span style={{ fontWeight: 700, fontFamily: 'monospace' }}>{sites.length}</span>
          <span style={{ fontSize: 11, color: '#B0BEC5' }}>سایت | ماه {month}</span>
        </Panel>
      </div>

      {/* left rail */}
      <div
        style={{
          position: 'absolute',
          left: 14,
          top: '50%',
          transform: 'translateY(-50%)',
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
        }}
      >
        {[
          { icon: <Bell size={18} />, badge: '', title: 'هشدارها' },
          { icon: <Coins size={18} />, badge: '', title: 'مالی' },
          { icon: <Settings size={18} />, badge: '', title: 'تنظیمات' },
          { icon: <Camera size={18} />, badge: '', title: 'تصویر' },
          { icon: <HelpCircle size={18} />, badge: '', title: 'راهنما' },
        ].map((b, i) => (
          <button
            key={i}
            title={b.title}
            style={{
              width: 44,
              height: 44,
              borderRadius: '50%',
              border: '1px solid rgba(255,255,255,0.15)',
              background: 'rgba(255,255,255,0.12)',
              backdropFilter: 'blur(8px)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
            }}
          >
            {b.icon}
          </button>
        ))}
      </div>

      {/* bottom dashboard */}
      <div style={{ position: 'absolute', bottom: 12, left: 12, right: 12 }}>
        <Panel
          style={{
            padding: '10px 18px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 18,
            flexWrap: 'wrap',
          }}
        >
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            {currentNormal && (
              <>
                <StatChip
                  icon={<Thermometer size={16} style={{ color: '#FF8A65' }} />}
                  value={`${currentNormal.tavg_c.toFixed(1)}°C`}
                />
                <StatChip
                  icon={<Sun size={16} style={{ color: '#FFD54F' }} />}
                  value={`ET0 ${currentNormal.et0_mm.toFixed(1)}mm`}
                />
                <StatChip
                  icon={<CloudRain size={16} style={{ color: '#64B5F6' }} />}
                  value={`${currentNormal.precip_mm.toFixed(0)}mm`}
                />
                <StatChip
                  icon={<Wind size={16} style={{ color: '#81C784' }} />}
                  value={`${selectedSite?.koppen || '—'}`}
                />
              </>
            )}
          </div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <StatChip icon={<Users size={16} style={{ color: '#90CAF9' }} />} value="30/100" />
            <div style={{ display: 'flex', gap: 6 }}>
              {['$', '✂', '🔨', '🚜'].map((t, i) => (
                <div
                  key={i}
                  style={{
                    width: 38,
                    height: 38,
                    borderRadius: 8,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'rgba(255,255,255,0.08)',
                    fontSize: 16,
                    cursor: 'pointer',
                    borderBottom: i === 0 ? '3px solid #4CAF50' : 'none',
                  }}
                >
                  {t}
                </div>
              ))}
            </div>
            <StatChip icon={<Coins size={16} style={{ color: '#FFD700' }} />} value="7 184 593" />
            <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
              <button
                onClick={() => setPlaying(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: playing ? '#B0BEC5' : '#fff',
                  cursor: 'pointer',
                }}
              >
                <Pause size={16} />
              </button>
              <button
                onClick={() => {
                  setPlaying(true);
                  setSpeed(1);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: playing && speed === 1 ? '#fff' : '#B0BEC5',
                  cursor: 'pointer',
                }}
              >
                <Play size={16} />
              </button>
              <button
                onClick={() => {
                  setPlaying(true);
                  setSpeed(3);
                }}
                style={{
                  background: 'none',
                  border: 'none',
                  color: playing && speed > 1 ? '#fff' : '#B0BEC5',
                  cursor: 'pointer',
                }}
              >
                <FastForward size={16} />
              </button>
              <span style={{ fontSize: 11, color: '#B0BEC5', fontFamily: 'monospace' }}>
                ماه {month}
              </span>
            </div>
          </div>
        </Panel>
      </div>

      {/* right panel: manage + real data */}
      <div
        style={{
          position: 'absolute',
          top: 64,
          right: 12,
          bottom: 74,
          width: 350,
          display: 'flex',
          flexDirection: 'column',
          gap: 10,
          overflow: 'hidden',
        }}
      >
        <Panel style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            {(
              [
                ['plant', 'کاشت / AquaCrop'],
                ['irrigate', 'آبیاری'],
                ['analyze', 'تحلیل محصول'],
              ] as const
            ).map(([k, label]) => (
              <button
                key={k}
                onClick={() => setPanelTab(k)}
                style={{
                  flex: 1,
                  padding: '10px 6px',
                  background: panelTab === k ? 'rgba(76,175,80,0.25)' : 'transparent',
                  border: 'none',
                  borderBottom: panelTab === k ? '2px solid #4CAF50' : '2px solid transparent',
                  color: panelTab === k ? '#fff' : '#B0BEC5',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {label}
              </button>
            ))}
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: 12, fontSize: 12.5 }}>
            {panelTab === 'plant' && (
              <>
                <div style={{ color: '#B0BEC5', marginBottom: 8 }}>
                  محصولات (KC از دیتابیس دستی):
                </div>
                {crops.slice(0, 8).map((c) => (
                  <div
                    key={c.species_id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      padding: '6px 4px',
                      borderBottom: '1px solid rgba(255,255,255,0.06)',
                    }}
                  >
                    <span>{c.scientific_name || c.species_id}</span>
                    <span style={{ fontFamily: 'monospace', color: '#81C784' }}>KC {c.kc_mid}</span>
                  </div>
                ))}
                <button
                  onClick={() =>
                    runMotor('aquacrop', {
                      crop_name: 'wheat',
                      planting_date: '2022-11-05',
                      sim_start: '2022-11-01',
                      sim_end: '2023-06-30',
                    })
                  }
                  disabled={running !== null}
                  style={{
                    width: '100%',
                    marginTop: 10,
                    padding: '10px',
                    borderRadius: 10,
                    border: 'none',
                    background: 'linear-gradient(135deg, #4CAF50, #388E3C)',
                    color: '#fff',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                  }}
                >
                  {running === 'aquacrop' ? (
                    <Loader2 size={15} className="spin" />
                  ) : (
                    <Sprout size={15} />
                  )}
                  اجرای AquaCrop برای {siteId}
                </button>
              </>
            )}
            {panelTab === 'irrigate' && (
              <>
                <div style={{ color: '#B0BEC5', marginBottom: 8 }}>
                  ET0 ماهانه (نرمال اقلیمی سایت):
                </div>
                {normals.length > 0 && (
                  <ResponsiveContainer width="100%" height={160}>
                    <LineChart data={chartData}>
                      <CartesianGrid stroke="rgba(255,255,255,0.08)" />
                      <XAxis dataKey="month" tick={{ fill: '#B0BEC5', fontSize: 10 }} />
                      <YAxis tick={{ fill: '#B0BEC5', fontSize: 10 }} />
                      <Tooltip
                        contentStyle={{
                          background: '#16181f',
                          border: '1px solid rgba(255,255,255,0.15)',
                          borderRadius: 8,
                        }}
                      />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="et0"
                        stroke="#FF8A65"
                        name="ET0 (mm)"
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="precip"
                        stroke="#64B5F6"
                        name="بارش (mm)"
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                )}
                <button
                  onClick={() => runMotor('irrigation', { crop: 'wheat', season_days: 120 })}
                  disabled={running !== null}
                  style={{
                    width: '100%',
                    marginTop: 10,
                    padding: '10px',
                    borderRadius: 10,
                    border: 'none',
                    background: 'linear-gradient(135deg, #29B6F6, #0288D1)',
                    color: '#fff',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                  }}
                >
                  {running === 'irrigation' ? (
                    <Loader2 size={15} className="spin" />
                  ) : (
                    <Droplets size={15} />
                  )}
                  محاسبه‌ی برنامه‌ی آبیاری
                </button>
              </>
            )}
            {panelTab === 'analyze' && (
              <>
                <div style={{ color: '#B0BEC5', marginBottom: 8 }}>
                  مشاور انتخاب محصول — ارزیابی بر اساس خاک/اقلیم سایت:
                </div>
                <button
                  onClick={() => runMotor('crop_advisor')}
                  disabled={running !== null}
                  style={{
                    width: '100%',
                    padding: '10px',
                    borderRadius: 10,
                    border: 'none',
                    background: 'linear-gradient(135deg, #8b5cf6, #6366f1)',
                    color: '#fff',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: 8,
                  }}
                >
                  {running === 'crop_advisor' ? (
                    <Loader2 size={15} className="spin" />
                  ) : (
                    <TrendingUp size={15} />
                  )}
                  تحلیل suitability برای {siteId}
                </button>
                {normals.length > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <div style={{ color: '#B0BEC5', marginBottom: 6 }}>دمای میانگین ماهانه:</div>
                    <ResponsiveContainer width="100%" height={150}>
                      <LineChart data={chartData}>
                        <CartesianGrid stroke="rgba(255,255,255,0.08)" />
                        <XAxis dataKey="month" tick={{ fill: '#B0BEC5', fontSize: 10 }} />
                        <YAxis tick={{ fill: '#B0BEC5', fontSize: 10 }} />
                        <Tooltip
                          contentStyle={{
                            background: '#16181f',
                            border: '1px solid rgba(255,255,255,0.15)',
                            borderRadius: 8,
                          }}
                        />
                        <Line
                          type="monotone"
                          dataKey="tavg"
                          stroke="#FFD54F"
                          name="Tavg (°C)"
                          dot={false}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}
              </>
            )}
          </div>
        </Panel>

        {/* live result */}
        {running && (
          <Panel style={{ padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Loader2 size={15} className="spin" style={{ color: '#4CAF50' }} />
            <span style={{ fontSize: 12 }}>
              در حال اجرای {running} روی {siteId}… (CPU)
            </span>
          </Panel>
        )}
        {result && (
          <Panel style={{ padding: '12px 14px', maxHeight: 260, overflowY: 'auto' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              {result.result?.status === 'completed' ? (
                <CheckCircle size={16} style={{ color: '#4CAF50' }} />
              ) : (
                <XCircle size={16} style={{ color: '#FF5252' }} />
              )}
              <strong style={{ fontSize: 13 }}>
                {result.motor} — {result.result?.status}
              </strong>
            </div>
            {result.provenance && (
              <div
                style={{
                  fontSize: 11,
                  color: '#B0BEC5',
                  marginBottom: 8,
                  direction: 'ltr',
                  textAlign: 'left',
                }}
              >
                {JSON.stringify(result.provenance)}
              </div>
            )}
            {result.result?.summary && (
              <pre
                dir="ltr"
                style={{
                  fontSize: 11,
                  whiteSpace: 'pre-wrap',
                  background: 'rgba(255,255,255,0.05)',
                  padding: 10,
                  borderRadius: 8,
                  margin: 0,
                }}
              >
                {JSON.stringify(result.result.summary, null, 2)}
              </pre>
            )}
            {result.result?.error_message && (
              <div style={{ color: '#FF8A80', fontSize: 12, marginTop: 6 }}>
                {result.result.error_message}
              </div>
            )}
          </Panel>
        )}
      </div>
    </div>
  );
}
