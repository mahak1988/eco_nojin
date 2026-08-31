import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import { Sprout, TreePine, Bird, Utensils } from 'lucide-react';
import data from '../../data/scientificData.json';

interface Props {
  selectedCrop: string | null;
  selectedLivestock: string | null;
  selectedPoultry: string | null;
  onSelectCrop: (id: string | null) => void;
  onSelectLivestock: (id: string | null) => void;
  onSelectPoultry: (id: string | null) => void;
}

export const CropsPanel = memo(function CropsPanel({
  selectedCrop,
  selectedLivestock,
  selectedPoultry,
  onSelectCrop,
  onSelectLivestock,
  onSelectPoultry,
}: Props) {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const cardStyle = {
    background: 'rgba(0,0,0,0.5)',
    backdropFilter: 'blur(15px)',
    padding: '12px',
    borderRadius: '12px',
    border: '1px solid rgba(255,255,255,0.1)',
    marginBottom: '10px',
  };

  const headerStyle = {
    fontSize: '11px',
    color: 'rgba(255,255,255,0.6)',
    marginBottom: '8px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  };

  const chipStyle = (active: boolean, color: string) => ({
    padding: '8px 12px',
    borderRadius: '10px',
    background: active ? `${color}30` : 'rgba(255,255,255,0.05)',
    border: `1px solid ${active ? color : 'rgba(255,255,255,0.1)'}`,
    color: active ? 'white' : 'rgba(255,255,255,0.7)',
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: active ? 700 : 500,
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    transition: 'all 0.2s',
  });

  return (
    <div style={{ width: '100%' }}>
      {/* Crops */}
      <div style={cardStyle}>
        <div style={headerStyle}>
          <Sprout size={12} color="#10b981" />
          {isFa ? 'محصولات' : 'Crops'}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {data.crops.map((c) => (
            <button
              key={c.id}
              style={chipStyle(selectedCrop === c.id, '#10b981')}
              onClick={() => onSelectCrop(selectedCrop === c.id ? null : c.id)}
            >
              <span>{c.emoji}</span>
              <span>{isFa ? c.fa : c.name}</span>
            </button>
          ))}
        </div>
        {selectedCrop &&
          (() => {
            const c = data.crops.find((x) => x.id === selectedCrop)!;
            return (
              <div
                style={{
                  marginTop: '10px',
                  padding: '10px',
                  background: 'rgba(16,185,129,0.1)',
                  borderRadius: '8px',
                  fontSize: '11px',
                }}
              >
                <div style={{ fontWeight: 700, marginBottom: '4px' }}>
                  📊 {isFa ? 'مشخصات' : 'Details'}:
                </div>
                <div>
                  💧 {isFa ? 'نیاز آبی' : 'Water'}: {c.waterNeed} mm
                </div>
                <div>
                  🌱 {isFa ? 'عمق ریشه' : 'Roots'}: {c.rootDepth} cm
                </div>
                <div>📈 Kc: {c.kc.join(' → ')}</div>
              </div>
            );
          })()}
      </div>

      {/* Livestock */}
      <div style={cardStyle}>
        <div style={headerStyle}>
          <Utensils size={12} color="#f59e0b" />
          {isFa ? 'دام' : 'Livestock'}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {data.livestock.map((l) => (
            <button
              key={l.id}
              style={chipStyle(selectedLivestock === l.id, '#f59e0b')}
              onClick={() => onSelectLivestock(selectedLivestock === l.id ? null : l.id)}
            >
              <span>{l.emoji}</span>
              <span>{isFa ? l.fa : l.name}</span>
            </button>
          ))}
        </div>
        {selectedLivestock &&
          (() => {
            const l = data.livestock.find((x) => x.id === selectedLivestock)!;
            return (
              <div
                style={{
                  marginTop: '10px',
                  padding: '10px',
                  background: 'rgba(245,158,11,0.1)',
                  borderRadius: '8px',
                  fontSize: '11px',
                }}
              >
                <div>
                  💧 {isFa ? 'آب روزانه' : 'Water/day'}: {l.waterPerDay} L
                </div>
                <div>
                  🌾 {isFa ? 'چرا' : 'Grazing'}: {l.grazingArea} ha/head
                </div>
              </div>
            );
          })()}
      </div>

      {/* Poultry */}
      <div style={cardStyle}>
        <div style={headerStyle}>
          <Bird size={12} color="#ec4899" />
          {isFa ? 'طیور' : 'Poultry'}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {data.poultry.map((p) => (
            <button
              key={p.id}
              style={chipStyle(selectedPoultry === p.id, '#ec4899')}
              onClick={() => onSelectPoultry(selectedPoultry === p.id ? null : p.id)}
            >
              <span>{p.emoji}</span>
              <span>{isFa ? p.fa : p.name}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
});
