import { useState, memo } from 'react';
import { useTranslation } from 'react-i18next';
import { Hammer, Trash2, Pencil, Square, Navigation, MousePointer2 } from 'lucide-react';
import data from '../../data/scientificData.json';

export interface PlacedOperation {
  id: string;
  type: string;
  x: number;
  y: number;
  label: string;
}

export interface PolygonArea {
  id: string;
  points: Array<{ x: number; y: number }>;
  name: string;
  color: string;
  area?: number;
}

interface Props {
  operations: PlacedOperation[];
  polygons: PolygonArea[];
  onAddOperation: (op: PlacedOperation) => void;
  onMoveOperation: (id: string, x: number, y: number) => void;
  onDeleteOperation: (id: string) => void;
  onAddPolygon: (poly: PolygonArea) => void;
  onDeletePolygon: (id: string) => void;
  mode: 'select' | 'move' | 'draw-polygon';
  onModeChange: (mode: 'select' | 'move' | 'draw-polygon') => void;
  currentDrawing: Array<{ x: number; y: number }>;
  onDrawingUpdate: (points: Array<{ x: number; y: number }>) => void;
  onFinishPolygon: () => void;
}

export const EngineeringOpsPanel = memo(function EngineeringOpsPanel({
  operations,
  polygons,
  onAddOperation,
  onMoveOperation,
  onDeleteOperation,
  onAddPolygon,
  onDeletePolygon,
  mode,
  onModeChange,
  currentDrawing,
  onDrawingUpdate,
  onFinishPolygon,
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

  const totalCost = operations.reduce((sum, op) => {
    const def = data.engineeringOps.find((d) => d.id === op.type);
    return sum + (def?.cost || 0);
  }, 0);

  return (
    <div style={{ width: '100%' }}>
      {/* Tool Mode Selector */}
      <div style={cardStyle}>
        <div
          style={{
            fontSize: '11px',
            color: 'rgba(255,255,255,0.6)',
            marginBottom: '8px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {isFa ? 'حالت ابزار (۴ حالت)' : 'Tool Mode (4 modes)'}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '6px' }}>
          <button
            onClick={() => onModeChange('select')}
            style={{
              padding: '12px 8px',
              borderRadius: '10px',
              background: mode === 'select' ? '#10b981' : 'rgba(255,255,255,0.05)',
              color: mode === 'select' ? 'white' : 'rgba(255,255,255,0.7)',
              border: mode === 'select' ? 'none' : '1px solid rgba(255,255,255,0.1)',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <MousePointer2 size={18} />
            <span>{isFa ? 'چرخش/انتخاب' : 'Orbit/Select'}</span>
          </button>
          <button
            onClick={() => onModeChange('draw-polygon')}
            style={{
              padding: '12px 8px',
              borderRadius: '10px',
              background: mode === 'draw-polygon' ? '#f59e0b' : 'rgba(255,255,255,0.05)',
              color: mode === 'draw-polygon' ? 'white' : 'rgba(255,255,255,0.7)',
              border: mode === 'draw-polygon' ? 'none' : '1px solid rgba(255,255,255,0.1)',
              cursor: 'pointer',
              fontSize: '12px',
              fontWeight: 600,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
            }}
          >
            <Pencil size={18} />
            <span>{isFa ? 'ترسیم محدوده' : 'Draw Area'}</span>
          </button>
        </div>

        {mode === 'draw-polygon' && (
          <div
            style={{
              marginTop: '8px',
              padding: '10px',
              background: 'rgba(245, 158, 11, 0.15)',
              borderRadius: '8px',
              fontSize: '11px',
              color: '#fbbf24',
            }}
          >
            💡 {isFa ? 'روی زمین کلیک کنید تا نقطه اضافه شود' : 'Click on terrain to add points'}
            <div style={{ display: 'flex', gap: '6px', marginTop: '8px' }}>
              <button
                onClick={onFinishPolygon}
                disabled={currentDrawing.length < 3}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '6px',
                  background: currentDrawing.length >= 3 ? '#f59e0b' : 'rgba(255,255,255,0.1)',
                  color: 'white',
                  border: 'none',
                  cursor: currentDrawing.length >= 3 ? 'pointer' : 'not-allowed',
                  fontSize: '11px',
                  fontWeight: 600,
                }}
              >
                ✓{' '}
                {isFa
                  ? `اتمام (${currentDrawing.length} نقطه)`
                  : `Finish (${currentDrawing.length})`}
              </button>
              <button
                onClick={() => onDrawingUpdate([])}
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '6px',
                  background: 'rgba(239, 68, 68, 0.2)',
                  color: '#fca5a5',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '11px',
                }}
              >
                ✕ {isFa ? 'پاک' : 'Clear'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Engineering Operations - click to enter place-op mode */}
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
          <Hammer size={12} color="#8b5cf6" />
          {isFa ? 'عملیات مهندسی (کلیک برای جانمایی)' : 'Engineering Ops (click to place)'}
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {data.engineeringOps.map((op) => (
            <button
              key={op.id}
              onClick={() => {
                // Enter place-op mode
                onModeChange('select'); // Keep as select to preserve OrbitControls
                // Create operation and place in center of terrain as default
                const newOp: PlacedOperation = {
                  id: 'op-' + Date.now(),
                  type: op.id,
                  x: 0, // center
                  y: 0, // center
                  label: isFa ? op.fa : op.name,
                };
                onAddOperation(newOp);
              }}
              style={{
                padding: '12px',
                borderRadius: '10px',
                textAlign: 'start',
                background: 'rgba(255,255,255,0.03)',
                border: '1px solid rgba(255,255,255,0.1)',
                color: 'white',
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '24px' }}>{op.emoji}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '13px' }}>{isFa ? op.fa : op.name}</div>
                  <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.5)' }}>
                    💰 ${op.cost.toLocaleString()} •{' '}
                    <Navigation size={10} style={{ display: 'inline' }} />{' '}
                    {isFa ? 'کلیک برای افزودن' : 'Click to add'}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Placed Operations List */}
      {operations.length > 0 && (
        <div style={cardStyle}>
          <div
            style={{
              fontSize: '11px',
              color: 'rgba(255,255,255,0.6)',
              marginBottom: '8px',
              textTransform: 'uppercase',
              display: 'flex',
              justifyContent: 'space-between',
            }}
          >
            <span>
              {isFa ? `جانمایی شده (${operations.length})` : `Placed (${operations.length})`}
            </span>
            <span style={{ color: '#10b981', fontWeight: 700 }}>${totalCost.toLocaleString()}</span>
          </div>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '4px',
              maxHeight: '200px',
              overflowY: 'auto',
            }}
          >
            {operations.map((op) => {
              const def = data.engineeringOps.find((d) => d.id === op.type);
              return (
                <div
                  key={op.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '8px',
                    background: 'rgba(139, 92, 246, 0.1)',
                    borderRadius: '8px',
                    fontSize: '11px',
                    border: '1px solid rgba(139, 92, 246, 0.3)',
                  }}
                >
                  <span style={{ fontSize: '16px' }}>{def?.emoji}</span>
                  <span style={{ flex: 1, color: 'white', fontWeight: 600 }}>{op.label}</span>
                  <span
                    style={{
                      color: 'rgba(255,255,255,0.5)',
                      fontSize: '10px',
                      fontFamily: 'monospace',
                    }}
                  >
                    [{op.x.toFixed(1)},{op.y.toFixed(1)}]
                  </span>
                  <button
                    onClick={() => onDeleteOperation(op.id)}
                    style={{
                      padding: '4px 6px',
                      borderRadius: '4px',
                      border: 'none',
                      background: 'rgba(239, 68, 68, 0.3)',
                      color: '#fca5a5',
                      cursor: 'pointer',
                    }}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Polygons List */}
      {polygons.length > 0 && (
        <div style={cardStyle}>
          <div
            style={{
              fontSize: '11px',
              color: 'rgba(255,255,255,0.6)',
              marginBottom: '8px',
              textTransform: 'uppercase',
            }}
          >
            {isFa ? `محدوده‌ها (${polygons.length})` : `Polygons (${polygons.length})`}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {polygons.map((poly) => (
              <div
                key={poly.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px',
                  background: `${poly.color}15`,
                  borderRadius: '8px',
                  fontSize: '11px',
                  border: `1px solid ${poly.color}40`,
                }}
              >
                <Square size={14} style={{ color: poly.color }} />
                <span style={{ flex: 1, color: 'white', fontWeight: 600 }}>{poly.name}</span>
                <span style={{ color: 'rgba(255,255,255,0.5)' }}>
                  {poly.points.length} pts • {poly.area?.toFixed(0) || 0}m²
                </span>
                <button
                  onClick={() => onDeletePolygon(poly.id)}
                  style={{
                    padding: '4px 6px',
                    borderRadius: '4px',
                    border: 'none',
                    background: 'rgba(239, 68, 68, 0.3)',
                    color: '#fca5a5',
                    cursor: 'pointer',
                  }}
                >
                  <Trash2 size={12} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Instructions */}
      <div
        style={{
          padding: '12px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(59, 130, 246, 0.1))',
          border: '1px solid rgba(16, 185, 129, 0.2)',
          fontSize: '11px',
          color: 'rgba(255,255,255,0.8)',
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: '6px', color: '#10b981' }}>
          💡 {isFa ? 'راهنما' : 'How to use'}
        </div>
        <div style={{ lineHeight: '1.6' }}>
          🖱️ <b>{isFa ? 'چرخش' : 'Rotate'}</b>: {isFa ? 'کلیک چپ + درگ' : 'Left click + drag'}
          <br />
          🔍 <b>{isFa ? 'زوم' : 'Zoom'}</b>: {isFa ? 'اسکرول موس' : 'Mouse wheel'}
          <br />✋ <b>{isFa ? 'جابجایی' : 'Pan'}</b>:{' '}
          {isFa ? 'کلیک راست + درگ' : 'Right click + drag'}
          <br />
          📐 <b>{isFa ? 'ترسیم' : 'Draw'}</b>:{' '}
          {isFa ? 'حالت ترسیم → کلیک روی زمین' : 'Draw mode → Click terrain'}
          <br />
          📍 <b>{isFa ? 'جانمایی' : 'Place'}</b>:{' '}
          {isFa ? 'انتخاب عملیات → کلیک' : 'Select op → Click'}
        </div>
      </div>
    </div>
  );
});

export function computePolygonArea(
  points: Array<{ x: number; y: number }>,
  cellSize = 20 / 64
): number {
  if (points.length < 3) return 0;
  let area = 0;
  for (let i = 0; i < points.length; i++) {
    const j = (i + 1) % points.length;
    area += points[i].x * points[j].y - points[j].x * points[i].y;
  }
  return (Math.abs(area) / 2) * cellSize * cellSize * 10000;
}
