import { useState, useCallback, memo } from 'react';
import { useTranslation } from 'react-i18next';
import { Mountain, Layers, Droplet, Map as MapIcon, Sparkles, Loader2 } from 'lucide-react';
import { generateTerrain } from '../../lib/terrainGenerator';
import type {
  TerrainConfig,
  TerrainData,
  LandformType,
  SoilType,
  SlopeClass,
  GeologyType,
} from '../../lib/terrainGenerator';

const LANDFORMS: Array<{ value: LandformType; label: string; fa: string; icon: string }> = [
  { value: 'plain', label: 'Plain', fa: 'دشت', icon: '🏞️' },
  { value: 'foothill', label: 'Foothill', fa: 'کوهپایه', icon: '⛰️' },
  { value: 'mountain', label: 'Mountain', fa: 'کوهستان', icon: '🏔️' },
  { value: 'desert', label: 'Desert', fa: 'بیابان', icon: '🏜️' },
  { value: 'rocky', label: 'Rocky', fa: 'سنگلاخ', icon: '🪨' },
  { value: 'rivervalley', label: 'River Valley', fa: 'آبراهه', icon: '🌊' },
  { value: 'plateau', label: 'Plateau', fa: 'فلات', icon: '🗻' },
  { value: 'canyon', label: 'Canyon', fa: 'تنگه', icon: '🏞️' },
  { value: 'coastal', label: 'Coastal', fa: 'ساحلی', icon: '🏖️' },
  { value: 'volcanic', label: 'Volcanic', fa: 'آتشفشانی', icon: '🌋' },
  { value: 'wetland', label: 'Wetland', fa: 'تالاب', icon: '🦆' },
  { value: 'karst', label: 'Karst', fa: 'کارستی', icon: '🕳️' },
];

const SOILS: Array<{ value: SoilType; label: string; fa: string; emoji: string }> = [
  { value: 'sand', label: 'Sand', fa: 'شنی', emoji: '🏖️' },
  { value: 'loam', label: 'Loam', fa: 'لومی', emoji: '🌱' },
  { value: 'clay', label: 'Clay', fa: 'رسی', emoji: '🧱' },
  { value: 'silt', label: 'Silt', fa: 'سیلتی', emoji: '🏺' },
  { value: 'gravel', label: 'Gravel', fa: 'سنگریزه', emoji: '⚪' },
  { value: 'peat', label: 'Peat', fa: 'پیت', emoji: '🟫' },
  { value: 'permafrost', label: 'Permafrost', fa: 'یخبندان', emoji: '❄️' },
];

const SLOPES: Array<{ value: SlopeClass; label: string; fa: string }> = [
  { value: 'flat', label: 'Flat', fa: 'مسطح' },
  { value: 'gentle', label: 'Gentle', fa: 'ملایم' },
  { value: 'moderate', label: 'Moderate', fa: 'متوسط' },
  { value: 'steep', label: 'Steep', fa: 'تند' },
  { value: 'very_steep', label: 'Very Steep', fa: 'بسیار تند' },
];

const GEOLOGIES: Array<{ value: GeologyType; label: string; fa: string; emoji: string }> = [
  { value: 'alluvium', label: 'Alluvium', fa: 'آبرفت', emoji: '💧' },
  { value: 'limestone', label: 'Limestone', fa: 'آهکی', emoji: '🪨' },
  { value: 'granite', label: 'Granite', fa: 'گرانیت', emoji: '⛰️' },
  { value: 'volcanic', label: 'Volcanic', fa: 'آذرین', emoji: '🌋' },
  { value: 'shale', label: 'Shale', fa: 'شیل', emoji: '📜' },
  { value: 'basalt', label: 'Basalt', fa: 'بازالت', emoji: '⚫' },
  { value: 'sandstone', label: 'Sandstone', fa: 'ماسه‌سنگ', emoji: '🟡' },
];

const Chip = memo(function Chip({
  active,
  onClick,
  children,
  color = '#10b981',
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  color?: string;
}) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '8px 12px',
        borderRadius: '8px',
        border: `1.5px solid ${active ? color : 'rgba(255,255,255,0.1)'}`,
        background: active ? `${color}25` : 'rgba(255,255,255,0.03)',
        color: active ? 'white' : 'rgba(255,255,255,0.7)',
        fontSize: '12px',
        fontWeight: active ? 600 : 500,
        cursor: 'pointer',
        display: 'inline-flex',
        alignItems: 'center',
        gap: '5px',
        transition: 'all 0.15s',
      }}
    >
      {children}
    </button>
  );
});

export default function TerrainBuilder({ onGenerate }: { onGenerate: (d: TerrainData) => void }) {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const [config, setConfig] = useState<TerrainConfig>({
    landform: 'foothill',
    soil: 'loam',
    slope: 'moderate',
    geology: 'alluvium',
    size: 64,
    seed: 0,
    hasWaterway: false,
  });
  const [generating, setGenerating] = useState(false);

  const update = <K extends keyof TerrainConfig>(key: K, value: TerrainConfig[K]) =>
    setConfig((p) => ({ ...p, [key]: value }));

  const handleGenerate = useCallback(() => {
    setGenerating(true);
    setTimeout(() => {
      const data = generateTerrain({ ...config, seed: Date.now() });
      onGenerate(data);
      setGenerating(false);
    }, 50);
  }, [config, onGenerate]);

  const Section = ({ title, icon, gradient, children }: any) => (
    <div
      style={{
        background: `linear-gradient(135deg, ${gradient}12, ${gradient}05)`,
        borderRadius: '12px',
        padding: '12px',
        marginBottom: '10px',
        border: `1px solid ${gradient}20`,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px' }}>
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '8px',
            background: `${gradient}25`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: gradient,
          }}
        >
          {icon}
        </div>
        <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)' }}>
          {title}
        </span>
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>{children}</div>
    </div>
  );

  return (
    <div
      style={{
        background: 'rgba(15, 23, 42, 0.9)',
        backdropFilter: 'blur(10px)',
        borderRadius: '12px',
        padding: '14px',
        border: '1px solid rgba(255,255,255,0.1)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '14px' }}>
        <Mountain size={22} color="#10b981" />
        <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 800 }}>
          {isFa ? 'سازنده زمین' : 'Terrain Builder'}
        </h3>
      </div>

      <Section
        title={isFa ? 'نوع زمین' : 'Landform'}
        icon={<Mountain size={14} />}
        gradient="#10b981"
      >
        {LANDFORMS.map((l) => (
          <Chip
            key={l.value}
            active={config.landform === l.value}
            onClick={() => update('landform', l.value)}
            color="#10b981"
          >
            <span>{l.icon}</span>
            <span>{isFa ? l.fa : l.label}</span>
          </Chip>
        ))}
      </Section>

      <Section title={isFa ? 'خاک' : 'Soil'} icon={<Layers size={14} />} gradient="#f59e0b">
        {SOILS.map((s) => (
          <Chip
            key={s.value}
            active={config.soil === s.value}
            onClick={() => update('soil', s.value)}
            color="#f59e0b"
          >
            <span>{s.emoji}</span>
            <span>{isFa ? s.fa : s.label}</span>
          </Chip>
        ))}
      </Section>

      <Section title={isFa ? 'شیب' : 'Slope'} icon={<MapIcon size={14} />} gradient="#3b82f6">
        {SLOPES.map((s) => (
          <Chip
            key={s.value}
            active={config.slope === s.value}
            onClick={() => update('slope', s.value)}
            color="#3b82f6"
          >
            <span>{isFa ? s.fa : s.label}</span>
          </Chip>
        ))}
      </Section>

      <Section
        title={isFa ? 'زمین‌شناسی' : 'Geology'}
        icon={<Droplet size={14} />}
        gradient="#8b5cf6"
      >
        {GEOLOGIES.map((g) => (
          <Chip
            key={g.value}
            active={config.geology === g.value}
            onClick={() => update('geology', g.value)}
            color="#8b5cf6"
          >
            <span>{g.emoji}</span>
            <span>{isFa ? g.fa : g.label}</span>
          </Chip>
        ))}
      </Section>

      <button
        onClick={handleGenerate}
        disabled={generating}
        style={{
          width: '100%',
          padding: '14px',
          borderRadius: '10px',
          border: 'none',
          background: generating ? '#6b7280' : 'linear-gradient(135deg, #10b981, #3b82f6)',
          color: 'white',
          fontSize: '14px',
          fontWeight: 700,
          cursor: generating ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px',
          boxShadow: '0 4px 15px rgba(16, 185, 129, 0.3)',
        }}
      >
        {generating ? (
          <>
            <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
            <span>{isFa ? 'در حال تولید...' : 'Generating...'}</span>
          </>
        ) : (
          <>
            <Sparkles size={16} />
            <span>{isFa ? 'تولید زمین سه‌بعدی' : 'Generate 3D Terrain'}</span>
          </>
        )}
      </button>

      <style>{`@keyframes spin { from { transform: rotate(0) } to { transform: rotate(360deg) } }`}</style>
    </div>
  );
}
