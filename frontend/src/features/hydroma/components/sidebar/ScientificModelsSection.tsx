/**
 * ScientificModelsSection
 * ========================
 * Scientific models hub (RUSLE, RothC, AquaCrop, etc).
 *
 * @module features/hydroma/components/sidebar/ScientificModelsSection
 */

import { useTranslation } from 'react-i18next';
import { FlaskConical } from 'lucide-react';
import { ScientificHub } from '../../../../components/simulators/ScientificHub';
import { sidebarStyles } from './styles';

export function ScientificModelsSection() {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  return (
    <div style={sidebarStyles.sectionCyan}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '8px',
        }}
      >
        <FlaskConical size={16} color="#06b6d4" />
        <span
          style={{
            fontSize: '12px',
            color: '#06b6d4',
            fontWeight: 700,
            textTransform: 'uppercase',
          }}
        >
          {isFa ? 'مدل‌های علمی واقعی' : 'Real Scientific Models'}
        </span>
      </div>

      <div
        style={{
          fontSize: '10px',
          color: 'rgba(255,255,255,0.6)',
          marginBottom: '10px',
          lineHeight: '1.5',
        }}
      >
        {isFa
          ? 'RUSLE • RothC • AquaCrop • Pywr • HEC-RAS • SWAT+ • NSGA-II'
          : 'Erosion • Carbon • Crop • Water • Flood • Watershed • Optimization'}
      </div>

      <ScientificHub />
    </div>
  );
}
