/** Card tooltip — shows a tooltip on hover with glass style. */

import { useState, useRef } from 'react';

interface CardTooltipProps {
  content: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export default function CardTooltip({ content, children, className = '' }: CardTooltipProps) {
  const [visible, setVisible] = useState(false);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const triggerRef = useRef<HTMLDivElement>(null);

  const handleMouseEnter = () => {
    if (triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect();
      setPosition({
        x: rect.left + rect.width / 2,
        y: rect.top,
      });
    }
    setVisible(true);
  };

  const handleMouseLeave = () => {
    setVisible(false);
  };

  return (
    <div
      ref={triggerRef}
      className={`relative ${className}`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
      {visible && (
        <div
          className="glass-advanced fixed z-50 min-w-48 max-w-xs rounded-xl px-4 py-3 shadow-2xl"
          style={{
            left: `${position.x}px`,
            top: `${position.y - 12}px`,
            transform: 'translate(-50%, -100%)',
            pointerEvents: 'none',
          }}
        >
          <div className="text-center">{content}</div>
          <div
            className="absolute left-1/2 top-full -translate-x-1/2 border-8 border-transparent border-t-night-900"
            style={{ marginTop: '-1px' }}
          />
        </div>
      )}
    </div>
  );
}
