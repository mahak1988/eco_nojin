import { useState } from 'react';
import { Button, Tooltip } from 'antd';
import { PlayCircleOutlined, CloseOutlined } from '@ant-design/icons';
import { CinematicSimulator } from './CinematicSimulator';

/**
 * Floating button that opens the full cinematic simulator.
 * Safe to drop into any page without altering its structure.
 */
export function CinematicMode() {
  const [open, setOpen] = useState(false);

  if (open) {
    return (
      <div style={{ position: 'fixed', inset: 0, zIndex: 9999, background: '#000' }}>
        <Button
          danger
          icon={<CloseOutlined />}
          onClick={() => setOpen(false)}
          style={{ position: 'absolute', top: 16, left: 16, zIndex: 10000 }}
        >
          خروج از حالت سینمایی
        </Button>
        <CinematicSimulator />
      </div>
    );
  }

  return (
    <Tooltip title="شبیه‌ساز سینمایی" placement="top">
      <Button
        type="primary"
        shape="circle"
        size="large"
        icon={<PlayCircleOutlined />}
        onClick={() => setOpen(true)}
        style={{
          position: 'fixed',
          bottom: 30,
          left: 30,
          zIndex: 1000,
          width: 64,
          height: 64,
          fontSize: 28,
          boxShadow: '0 4px 20px rgba(64, 150, 255, 0.5)',
        }}
      />
    </Tooltip>
  );
}

export default CinematicMode;
