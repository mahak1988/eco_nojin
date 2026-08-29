import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import { Eye, EyeOff, Layers, Droplet, TreePine, Mountain } from 'lucide-react';

export type LayerType = 'surface' | 'soil' | 'bedrock' | 'moisture' | 'roots';

interface LayerConfig {
  id: LayerType;
  name: string;
  fa: string;
  icon: any;
  color: string;
  visible: boolean;
  opacity: number;
}

interface Props {
  layers: LayerConfig[];
  onToggleLayer: (id: LayerType) => void;
  onOpacityChange: (id: LayerType, opacity: number) => void;
}

export const LayerPanel = memo(function LayerPanel({ layers, onToggleLayer, onOpacityChange }: Props) {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  return (
    <div style={{
      position: 'absolute', top: '16px', left: '16px', zIndex: 10,
      background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(15px)',
      padding: '14px', borderRadius: '14px',
      border: '1px solid rgba(255,255,255,0.1)',
      minWidth: '220px',
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '8px',
        marginBottom: '12px', paddingBottom: '8px',
        borderBottom: '1px solid rgba(255,255,255,0.1)',
      }}>
        <Layers size={16} style={{ color: '#10b981' }} />
        <span style={{ fontSize: '13px', fontWeight: 700, color: 'white' }}>
          {isFa ? 'لایه‌های زمین' : 'Terrain Layers'}
        </span>
      </div>

      {layers.map(layer => {
        const Icon = layer.icon;
        return (
          <div
            key={layer.id}
            style={{
              padding: '8px 10px',
              borderRadius: '8px',
              marginBottom: '6px',
              background: layer.visible ? `${layer.color}15` : 'transparent',
              border: `1px solid ${layer.visible ? `${layer.color}40` : 'rgba(255,255,255,0.05)'}`,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            <div
              onClick={() => onToggleLayer(layer.id)}
              style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <div style={{
                width: '28px', height: '28px', borderRadius: '8px',
                background: `${layer.color}25`, color: layer.color,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <Icon size={14} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '12px', fontWeight: 600, color: 'white' }}>
                  {isFa ? layer.fa : layer.name}
                </div>
              </div>
              {layer.visible ? <Eye size={14} color={layer.color} /> : <EyeOff size={14} color="#666" />}
            </div>

            {layer.visible && (
              <div style={{ marginTop: '8px', paddingLeft: '36px' }}>
                <input
                  type="range"
                  min={0} max={1} step={0.05}
                  value={layer.opacity}
                  onChange={(e) => onOpacityChange(layer.id, parseFloat(e.target.value))}
                  style={{ width: '100%', accentColor: layer.color }}
                />
                <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)', marginTop: '2px' }}>
                  Opacity: {Math.round(layer.opacity * 100)}%
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
});
