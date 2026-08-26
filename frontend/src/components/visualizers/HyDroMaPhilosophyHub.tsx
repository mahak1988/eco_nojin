import React from 'react';
import { motion } from 'framer-motion';
import {
  Leaf, Droplets, Wind, Beef, Trees, Sprout,
  Database, Coins, Shield, Sparkles, Globe,
} from 'lucide-react';
import { Card, Button } from '../ui';

/**
 * هاب فلسفی HyDroMa
 * 
 * این کامپوننت تمام ماژول‌های پروژه را به‌صورت بصری به هم متصل می‌کند
 * و فلسفه "از قطره تا اقیانوس، از دانه تا جنگل" را نمایش می‌دهد.
 */

const ECOSYSTEM_NODES = [
  {
    id: 'soil',
    title: 'خاک زنده',
    icon: Sprout,
    color: '#8b7355',
    position: { top: '15%', left: '25%' },
    connections: ['water', 'carbon', 'crops'],
    metrics: { soc: '۱.۸ t/ha', ph: '۷.۲', moisture: '۳۵٪' },
  },
  {
    id: 'water',
    title: 'چرخه آب',
    icon: Droplets,
    color: '#3b82f6',
    position: { top: '15%', left: '75%' },
    connections: ['soil', 'crops', 'aquifer'],
    metrics: { infiltration: '۲۸۰ mm', runoff: '۱۲۰ mm', et: '۸۰ mm' },
  },
  {
    id: 'crops',
    title: 'محصول',
    icon: Leaf,
    color: '#22c55e',
    position: { top: '45%', left: '50%' },
    connections: ['soil', 'water', 'livestock', 'carbon'],
    metrics: { yield: '۴.۲ t/ha', wue: '۱.۸ kg/m³', ndvi: '۰.۷۵' },
  },
  {
    id: 'wind',
    title: 'باد و فرسایش',
    icon: Wind,
    color: '#f59e0b',
    position: { top: '45%', left: '10%' },
    connections: ['crops', 'soil', 'windbreak'],
    metrics: { speed: '۱۲ m/s', erosion: '۲۵ t/ha', risk: 'بالا' },
  },
  {
    id: 'windbreak',
    title: 'بادشکن',
    icon: Trees,
    color: '#15803d',
    position: { top: '45%', left: '90%' },
    connections: ['wind', 'crops', 'carbon'],
    metrics: { height: '۸ m', reduction: '۶۰٪', cost: '$۵K' },
  },
  {
    id: 'livestock',
    title: 'دام',
    icon: Beef,
    color: '#dc2626',
    position: { top: '75%', left: '25%' },
    connections: ['crops', 'soil', 'economy'],
    metrics: { herd: '۲۰ رأس', milk: '۳۰۰ L/d', manure: '۵۸۰ t/y' },
  },
  {
    id: 'carbon',
    title: 'کربن',
    icon: Globe,
    color: '#06b6d4',
    position: { top: '75%', left: '75%' },
    connections: ['soil', 'crops', 'blockchain'],
    metrics: { sequestration: '۵.۵ t CO₂', credits: '۴.۷', value: '$۳۲۰' },
  },
  {
    id: 'blockchain',
    title: 'بلاکچین',
    icon: Database,
    color: '#8b5cf6',
    position: { top: '90%', left: '50%' },
    connections: ['carbon', 'economy'],
    metrics: { network: 'Polygon', token: 'ERC-1155', gas: '~$۰.۰۱' },
  },
  {
    id: 'economy',
    title: 'اقتصاد',
    icon: Coins,
    color: '#f59e0b',
    position: { top: '90%', left: '15%' },
    connections: ['livestock', 'blockchain'],
    metrics: { revenue: '$۲۵.۵K', profit: '۸۷٪', roi: '۴ سال' },
  },
];

export const HyDroMaPhilosophyHub: React.FC = () => {
  const [selectedNode, setSelectedNode] = React.useState<string | null>('crops');
  const selectedData = ECOSYSTEM_NODES.find((n) => n.id === selectedNode);

  return (
    <Card
      title="🌍 HyDroMa Philosophy Hub"
      icon={<Sparkles size={20} />}
      subtitle="از قطره تا اقیانوس، از دانه تا جنگل"
    >
      <div style={{ position: 'relative', width: '100%', height: 600 }}>
        {/* SVG Connections */}
        <svg
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            pointerEvents: 'none',
          }}
        >
          {ECOSYSTEM_NODES.map((node) =>
            node.connections.map((targetId) => {
              const target = ECOSYSTEM_NODES.find((n) => n.id === targetId);
              if (!target) return null;
              const isHighlighted =
                selectedNode === node.id || selectedNode === target.id;
              return (
                <motion.line
                  key={`${node.id}-${targetId}`}
                  x1={`${parseFloat(node.position.left)}%`}
                  y1={`${parseFloat(node.position.top)}%`}
                  x2={`${parseFloat(target.position.left)}%`}
                  y2={`${parseFloat(target.position.top)}%`}
                  stroke={isHighlighted ? node.color : 'var(--color-border)'}
                  strokeWidth={isHighlighted ? 3 : 1}
                  strokeDasharray={isHighlighted ? '0' : '5,5'}
                  opacity={isHighlighted ? 1 : 0.3}
                  initial={{ pathLength: 0 }}
                  animate={{ pathLength: 1 }}
                  transition={{ duration: 1 }}
                />
              );
            })
          )}
        </svg>

        {/* Nodes */}
        {ECOSYSTEM_NODES.map((node) => {
          const Icon = node.icon;
          const isSelected = selectedNode === node.id;
          return (
            <motion.button
              key={node.id}
              onClick={() => setSelectedNode(node.id)}
              whileHover={{ scale: 1.15 }}
              whileTap={{ scale: 0.95 }}
              animate={isSelected ? { scale: [1, 1.1, 1] } : {}}
              transition={{ duration: 0.5, repeat: isSelected ? Infinity : 0 }}
              style={{
                position: 'absolute',
                top: node.position.top,
                left: node.position.left,
                transform: 'translate(-50%, -50%)',
                width: 70,
                height: 70,
                borderRadius: '50%',
                background: isSelected ? node.color : `${node.color}30`,
                border: `3px solid ${node.color}`,
                color: isSelected ? 'white' : node.color,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                boxShadow: isSelected ? `0 0 30px ${node.color}80` : 'none',
                zIndex: isSelected ? 10 : 1,
              }}
            >
              <Icon size={24} />
              <div
                style={{
                  fontSize: '0.625rem',
                  fontWeight: 600,
                  marginTop: 2,
                }}
              >
                {node.title}
              </div>
            </motion.button>
          );
        })}

        {/* Info Panel */}
        {selectedData && (
          <motion.div
            key={selectedData.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              position: 'absolute',
              bottom: 20,
              left: '50%',
              transform: 'translateX(-50%)',
              width: '80%',
              maxWidth: 500,
              background: 'var(--color-surface)',
              border: `2px solid ${selectedData.color}`,
              borderRadius: 'var(--radius-xl)',
              padding: '1.25rem',
              boxShadow: 'var(--shadow-lg)',
              zIndex: 20,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: '50%',
                  background: selectedData.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'white',
                }}
              >
                {React.createElement(selectedData.icon, { size: 24 })}
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>
                  {selectedData.title}
                </h3>
                <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                  متصل به: {selectedData.connections.join('، ')}
                </div>
              </div>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '0.5rem',
              }}
            >
              {Object.entries(selectedData.metrics).map(([key, value]) => (
                <div
                  key={key}
                  style={{
                    padding: '0.5rem',
                    background: `${selectedData.color}10`,
                    borderRadius: 'var(--radius-md)',
                    textAlign: 'center',
                  }}
                >
                  <div
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--color-text-tertiary)',
                      marginBottom: '0.25rem',
                    }}
                  >
                    {key}
                  </div>
                  <div
                    style={{
                      fontSize: '0.875rem',
                      fontWeight: 700,
                      color: selectedData.color,
                    }}
                  >
                    {value}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </Card>
  );
};
