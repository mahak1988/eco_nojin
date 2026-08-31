import { memo } from 'react';
import { useTranslation } from 'react-i18next';
import { Box, RotateCw, ZoomIn, ZoomOut, Camera, Map as MapIcon, Compass } from 'lucide-react';

export type ViewMode = '3d' | '2d-top' | '2d-side' | 'cross-section';

interface Props {
  viewMode: ViewMode;
  setViewMode: (mode: ViewMode) => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetCamera: () => void;
}

export const ViewControls = memo(function ViewControls({
  viewMode,
  setViewMode,
  onZoomIn,
  onZoomOut,
  onResetCamera,
}: Props) {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const modes: Array<{
    mode: ViewMode;
    icon: any;
    label: string;
    fa: string;
    hint: string;
    hintFa: string;
  }> = [
    {
      mode: '3d',
      icon: Compass,
      label: '3D Orbit',
      fa: 'سه‌بعدی چرخشی',
      hint: 'Drag to rotate',
      hintFa: 'درگ برای چرخش',
    },
    {
      mode: '2d-top',
      icon: MapIcon,
      label: 'Top View',
      fa: 'از بالا',
      hint: 'Fixed top',
      hintFa: 'بالای ثابت',
    },
    {
      mode: '2d-side',
      icon: Camera,
      label: 'Side View',
      fa: 'از کنار',
      hint: 'Profile view',
      hintFa: 'نمای پروفیل',
    },
    {
      mode: 'cross-section',
      icon: RotateCw,
      label: 'Cross-Section',
      fa: 'برش عرضی',
      hint: 'Cut view',
      hintFa: 'نمای برش',
    },
  ];

  const btnStyle = (active: boolean) => ({
    padding: '10px 14px',
    borderRadius: '10px',
    border: `1.5px solid ${active ? '#10b981' : 'rgba(255,255,255,0.1)'}`,
    background: active ? 'rgba(16, 185, 129, 0.2)' : 'rgba(0,0,0,0.4)',
    color: active ? '#10b981' : 'white',
    fontSize: '11px',
    fontWeight: active ? 700 : 500,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    transition: 'all 0.2s',
    backdropFilter: 'blur(10px)',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: '16px',
        right: '16px',
        zIndex: 10,
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
      }}
    >
      {/* View Mode Buttons */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(15px)',
          padding: '10px',
          borderRadius: '14px',
          border: '1px solid rgba(255,255,255,0.1)',
          minWidth: '180px',
        }}
      >
        <div
          style={{
            fontSize: '10px',
            color: 'rgba(255,255,255,0.6)',
            padding: '0 4px 6px 4px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            marginBottom: '4px',
          }}
        >
          {isFa ? 'حالت نمایش' : 'View Mode'}
        </div>
        {modes.map(({ mode, icon: Icon, label, fa, hint, hintFa }) => (
          <button key={mode} style={btnStyle(viewMode === mode)} onClick={() => setViewMode(mode)}>
            <Icon size={14} />
            <div style={{ flex: 1, textAlign: 'start' }}>
              <div>{isFa ? fa : label}</div>
              {viewMode === mode && (
                <div style={{ fontSize: '9px', opacity: 0.7, marginTop: '2px' }}>
                  {isFa ? hintFa : hint}
                </div>
              )}
            </div>
          </button>
        ))}
      </div>

      {/* Zoom Controls */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(15px)',
          padding: '10px',
          borderRadius: '14px',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
      >
        <div
          style={{
            fontSize: '10px',
            color: 'rgba(255,255,255,0.6)',
            padding: '0 4px 6px 4px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            marginBottom: '4px',
          }}
        >
          {isFa ? 'زوم و دوربین' : 'Zoom & Camera'}
        </div>
        <button style={btnStyle(false)} onClick={onZoomIn}>
          <ZoomIn size={14} /> <span>{isFa ? 'زوم نزدیک' : 'Zoom In'}</span>
        </button>
        <button style={btnStyle(false)} onClick={onZoomOut}>
          <ZoomOut size={14} /> <span>{isFa ? 'زوم دور' : 'Zoom Out'}</span>
        </button>
        <button style={btnStyle(false)} onClick={onResetCamera}>
          <RotateCw size={14} /> <span>{isFa ? 'بازنشانی' : 'Reset View'}</span>
        </button>
      </div>

      {/* Mouse controls hint */}
      <div
        style={{
          background: 'rgba(0,0,0,0.6)',
          backdropFilter: 'blur(15px)',
          padding: '10px',
          borderRadius: '14px',
          border: '1px solid rgba(255,255,255,0.1)',
          fontSize: '10px',
          color: 'rgba(255,255,255,0.7)',
          lineHeight: '1.6',
        }}
      >
        <div style={{ fontWeight: 700, color: '#10b981', marginBottom: '4px' }}>
          🖱️ {isFa ? 'کنترل موس' : 'Mouse Controls'}
        </div>
        <div>🖱️ {isFa ? 'چپ + درگ: چرخش' : 'Left + Drag: Rotate'}</div>
        <div>🖱️ {isFa ? 'اسکرول: زوم' : 'Scroll: Zoom'}</div>
        <div>🖱️ {isFa ? 'راست + درگ: حرکت' : 'Right + Drag: Pan'}</div>
      </div>
    </div>
  );
});
