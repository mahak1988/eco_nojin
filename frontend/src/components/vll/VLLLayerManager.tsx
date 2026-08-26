import React from 'react';
import { Card } from '../ui';
import { Mountain, Compass, Droplets, Leaf, Waves, AlertTriangle, Layers } from 'lucide-react';

interface VLLLayerManagerProps {
  activeLayers: Record<string, boolean>;
  onToggleLayer: (key: string) => void;
}

const LAYERS = [
  { key: 'dem', label: 'مدل ارتفاع (DEM)', icon: <Mountain size={16} />, color: '#8b7355' },
  { key: 'slope', label: 'نقشه شیب', icon: <Compass size={16} />, color: '#f59e0b' },
  { key: 'soil', label: 'نقشه خاک', icon: <Leaf size={16} />, color: '#84cc16' },
  { key: 'ndvi', label: 'شاخص NDVI', icon: <Leaf size={16} />, color: '#22c55e' },
  { key: 'water', label: 'رطوبت خاک', icon: <Droplets size={16} />, color: '#3b82f6' },
  { key: 'erosion', label: 'ریسک فرسایش', icon: <AlertTriangle size={16} />, color: '#ef4444' },
];

export const VLLLayerManager: React.FC<VLLLayerManagerProps> = ({ activeLayers, onToggleLayer }) => {
  return (
    <Card title="🗺️ لایه‌های GIS" icon={<Layers size={18} />} className="mb-4">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {LAYERS.map((layer) => (
          <button
            key={layer.key}
            onClick={() => onToggleLayer(layer.key)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.5rem',
              borderRadius: 'var(--radius-md)',
              border: `2px solid ${activeLayers[layer.key] ? layer.color : 'var(--color-border)'}`,
              background: activeLayers[layer.key] ? `${layer.color}15` : 'transparent',
              cursor: 'pointer',
              fontSize: '0.875rem',
              transition: 'all 0.2s',
            }}
          >
            <span style={{ color: layer.color }}>{layer.icon}</span>
            <span style={{ flex: 1, textAlign: 'right' }}>{layer.label}</span>
            <div
              style={{
                width: 16,
                height: 16,
                borderRadius: '50%',
                background: activeLayers[layer.key] ? layer.color : 'var(--color-border)',
              }}
            />
          </button>
        ))}
      </div>
    </Card>
  );
};


