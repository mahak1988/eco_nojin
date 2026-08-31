import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import { Tractor, AlertTriangle, Droplets, Wind } from 'lucide-react';
import data from '../../data/scientificData.json';

export interface OperationsState {
  plowingType: string;
  customDepth: number;
  avgSlope: number;
  avgErosion: number;
  avgRunoff: number;
  avgWindErosion: number;
}

interface Props {
  state: OperationsState;
  onChange: (state: OperationsState) => void;
  terrain?: any;
}

export const OperationsPanel = memo(function OperationsPanel({ state, onChange, terrain }: Props) {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const update = (patch: Partial<OperationsState>) => onChange({ ...state, ...patch });

  const cardStyle = {
    background: 'rgba(0,0,0,0.5)',
    backdropFilter: 'blur(15px)',
    padding: '12px',
    borderRadius: '12px',
    border: '1px solid rgba(255,255,255,0.1)',
    marginBottom: '10px',
  };

  // Find current plowing type info
  const currentPlowing =
    data.plowingTypes.find((p) => p.id === state.plowingType) || data.plowingTypes[0];
  const effectiveDepth = state.customDepth > 0 ? state.customDepth : currentPlowing.depth;

  return (
    <div style={{ width: '100%' }}>
      {/* Plowing Types */}
      <div style={cardStyle}>
        <div
          style={{
            fontSize: '11px',
            color: 'rgba(255,255,255,0.6)',
            marginBottom: '8px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <Tractor size={12} color="#f59e0b" />
          {isFa ? 'نوع شخم' : 'Plowing Type'}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {data.plowingTypes.map((p) => {
            const active = state.plowingType === p.id;
            return (
              <button
                key={p.id}
                onClick={() => update({ plowingType: p.id, customDepth: p.depth })}
                style={{
                  padding: '10px',
                  borderRadius: '10px',
                  textAlign: 'start',
                  background: active ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255,255,255,0.03)',
                  border: `1px solid ${active ? '#f59e0b' : 'rgba(255,255,255,0.1)'}`,
                  color: active ? 'white' : 'rgba(255,255,255,0.7)',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                <div style={{ fontWeight: 700, fontSize: '13px', marginBottom: '2px' }}>
                  {isFa ? p.fa : p.name}
                </div>
                <div
                  style={{
                    fontSize: '10px',
                    color: 'rgba(255,255,255,0.5)',
                    display: 'flex',
                    gap: '8px',
                  }}
                >
                  <span>⬇️ {p.depth}cm</span>
                  <span>⚠️ {(p.erosionRisk * 100).toFixed(0)}%</span>
                </div>
              </button>
            );
          })}
        </div>

        {/* Custom depth slider */}
        <div style={{ marginTop: '12px' }}>
          <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)', marginBottom: '6px' }}>
            {isFa ? 'عمق سفارشی' : 'Custom Depth'}:{' '}
            <span style={{ color: '#f59e0b', fontWeight: 700 }}>{effectiveDepth}cm</span>
          </div>
          <input
            type="range"
            min={0}
            max={50}
            step={1}
            value={state.customDepth > 0 ? state.customDepth : currentPlowing.depth}
            onChange={(e) => update({ customDepth: parseInt(e.target.value) })}
            style={{ width: '100%', accentColor: '#f59e0b' }}
          />
        </div>
      </div>

      {/* Erosion Metrics (from terrain) */}
      <div style={cardStyle}>
        <div
          style={{
            fontSize: '11px',
            color: 'rgba(255,255,255,0.6)',
            marginBottom: '8px',
            textTransform: 'uppercase',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <AlertTriangle size={12} color="#ef4444" />
          {isFa ? 'ریسک فرسایش' : 'Erosion Risk'}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {/* Water erosion (USLE) */}
          <div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '11px',
                marginBottom: '4px',
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#3b82f6' }}>
                <Droplets size={12} />
                {isFa ? 'فرسایش آبی (USLE)' : 'Water Erosion'}
              </span>
              <span style={{ color: 'white', fontWeight: 700 }}>
                {state.avgErosion.toFixed(2)} t/ha/yr
              </span>
            </div>
            <div
              style={{
                height: '6px',
                borderRadius: '3px',
                background: 'rgba(255,255,255,0.1)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  borderRadius: '3px',
                  width: `${Math.min(100, state.avgErosion * 5)}%`,
                  background:
                    state.avgErosion > 10
                      ? '#ef4444'
                      : state.avgErosion > 5
                        ? '#f59e0b'
                        : '#10b981',
                  transition: 'width 0.3s',
                }}
              />
            </div>
          </div>

          {/* Wind erosion */}
          <div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '11px',
                marginBottom: '4px',
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#a855f7' }}>
                <Wind size={12} />
                {isFa ? 'فرسایش بادی (RWEQ)' : 'Wind Erosion'}
              </span>
              <span style={{ color: 'white', fontWeight: 700 }}>
                {state.avgWindErosion.toFixed(3)} kg/m²
              </span>
            </div>
            <div
              style={{
                height: '6px',
                borderRadius: '3px',
                background: 'rgba(255,255,255,0.1)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  borderRadius: '3px',
                  width: `${Math.min(100, state.avgWindErosion * 100)}%`,
                  background: '#a855f7',
                  transition: 'width 0.3s',
                }}
              />
            </div>
          </div>

          {/* Runoff (SCS-CN) */}
          <div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                fontSize: '11px',
                marginBottom: '4px',
              }}
            >
              <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#06b6d4' }}>
                <Droplets size={12} />
                {isFa ? 'رواناب (SCS-CN)' : 'Runoff'}
              </span>
              <span style={{ color: 'white', fontWeight: 700 }}>
                {state.avgRunoff.toFixed(1)} mm
              </span>
            </div>
            <div
              style={{
                height: '6px',
                borderRadius: '3px',
                background: 'rgba(255,255,255,0.1)',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  borderRadius: '3px',
                  width: `${Math.min(100, state.avgRunoff * 2)}%`,
                  background: '#06b6d4',
                  transition: 'width 0.3s',
                }}
              />
            </div>
          </div>
        </div>

        {/* Warning if high erosion */}
        {state.avgErosion > 10 && (
          <div
            style={{
              marginTop: '10px',
              padding: '8px 10px',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              borderRadius: '8px',
              fontSize: '11px',
              color: '#fca5a5',
            }}
          >
            ⚠️{' '}
            {isFa
              ? 'ریسک فرسایش بالا! عملیات حفاظتی پیشنهاد می‌شود'
              : 'High erosion risk! Conservation practices recommended'}
          </div>
        )}
      </div>
    </div>
  );
});

export const defaultOperations: OperationsState = {
  plowingType: 'conventional',
  customDepth: 25,
  avgSlope: 5,
  avgErosion: 3.5,
  avgRunoff: 12,
  avgWindErosion: 0.05,
};
