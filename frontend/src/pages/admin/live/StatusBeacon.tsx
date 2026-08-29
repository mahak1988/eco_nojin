import { motion } from 'framer-motion';
import './LiveComponents.css';

interface StatusBeaconProps {
  status: 'online' | 'offline' | 'warning' | 'maintenance';
  label: string;
  size?: 'sm' | 'md' | 'lg';
  pulse?: boolean;
}

export default function StatusBeacon({ status, label, size = 'md', pulse = true }: StatusBeaconProps) {
  const colorMap = {
    online: '#10b981',
    offline: '#ef4444',
    warning: '#f59e0b',
    maintenance: '#8b5cf6',
  };

  const sizeMap = {
    sm: { beacon: 8, glow: 16, text: '11px' },
    md: { beacon: 12, glow: 24, text: '13px' },
    lg: { beacon: 16, glow: 32, text: '15px' },
  };

  const color = colorMap[status];
  const s = sizeMap[size];

  return (
    <div className="status-beacon-container">
      <div className="status-beacon-wrapper">
        {pulse && (
          <motion.div
            className="status-beacon-glow"
            style={{
              width: s.glow,
              height: s.glow,
              background: color,
            }}
            animate={{
              scale: [1, 1.5, 1],
              opacity: [0.6, 0, 0.6],
            }}
            transition={{
              duration: 2,
              repeat: Infinity,
              ease: 'easeInOut',
            }}
          />
        )}
        <div
          className="status-beacon-dot"
          style={{
            width: s.beacon,
            height: s.beacon,
            background: color,
            boxShadow: `0 0 ${s.beacon}px ${color}`,
          }}
        />
      </div>
      <span className="status-beacon-label" style={{ fontSize: s.text }}>
        {label}
      </span>
    </div>
  );
}
