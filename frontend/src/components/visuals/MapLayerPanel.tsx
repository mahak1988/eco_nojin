import { useLang } from '../../i18n/LanguageContext';
import { Layers, Mountain, Droplets, Leaf, type LucideIcon } from 'lucide-react';

type DataLayer = 'soil' | 'water' | 'carbon';

interface LayerConfig {
  key: DataLayer;
  icon: LucideIcon;
  labelFa: string;
  labelEn: string;
  color: string;
}

const LAYERS: LayerConfig[] = [
  { key: 'soil', icon: Mountain, labelFa: 'خاک', labelEn: 'Soil', color: '#d49b3f' },
  { key: 'water', icon: Droplets, labelFa: 'آب', labelEn: 'Water', color: '#2a9bb5' },
  { key: 'carbon', icon: Leaf, labelFa: 'کربن', labelEn: 'Carbon', color: '#2fb36b' },
];

interface MapLayerPanelProps {
  activeLayers: DataLayer[];
  onToggle: (layer: DataLayer) => void;
  className?: string;
}

export default function MapLayerPanel({ activeLayers, onToggle, className }: MapLayerPanelProps) {
  const { lang } = useLang();

  return (
    <div className={`glass glass-hover rounded-xl bg-[var(--color-night-900)] p-3 ${className || ''}`}>
      <div className="flex items-center gap-2 mb-2 px-1">
        <Layers className="h-3.5 w-3.5 text-[var(--color-night-200)]/60" aria-hidden />
        <span className="text-[10px] font-bold text-[var(--color-night-200)]/60">
          {lang === 'fa' ? 'لایه‌های داده' : 'Data Layers'}
        </span>
      </div>
      <div className="flex flex-col gap-1">
        {LAYERS.map((layer) => {
          const Icon = layer.icon;
          const isActive = activeLayers.includes(layer.key);
          return (
            <button
              key={layer.key}
              type="button"
              onClick={() => onToggle(layer.key)}
              className={`flex items-center gap-2 rounded-lg px-2 py-1.5 text-[11px] font-bold transition-all ${
                isActive
                  ? 'bg-white/10 text-[var(--color-night-100)]'
                  : 'text-[var(--color-night-200)]/50 hover:bg-white/5 hover:text-[var(--color-night-100)]'
              }`}
              aria-pressed={isActive}
            >
              <div
                className="h-2.5 w-2.5 rounded-full"
                style={{ backgroundColor: isActive ? layer.color : 'var(--color-night-200)' }}
                aria-hidden
              />
              <Icon className="h-3.5 w-3.5" aria-hidden />
              {lang === 'fa' ? layer.labelFa : layer.labelEn}
            </button>
          );
        })}
      </div>
    </div>
  );
}
