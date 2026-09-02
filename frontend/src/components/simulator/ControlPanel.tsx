import { Drawer, Slider, Switch, Segmented, Typography, Space } from 'antd';
import { useSimulatorStore, Weather, TimeOfDay } from './simulatorStore';
import { useState } from 'react';

const { Title, Text } = Typography;

const WEATHER_OPTIONS = [
  { value: 'clear', label: '☀️ صاف' },
  { value: 'rain',  label: '🌧️ باران' },
  { value: 'snow',  label: '❄️ برف' },
  { value: 'dust',  label: '🌫️ ریزگرد' },
  { value: 'storm', label: '⛈️ طوفان' },
];

const TIME_OPTIONS = [
  { value: 'dawn',  label: '🌅 طلوع' },
  { value: 'day',   label: '☀️ روز' },
  { value: 'dusk',  label: '🌇 غروب' },
  { value: 'night', label: '🌙 شب' },
];

const QUALITY_OPTIONS = [
  { value: 'low',    label: 'کم' },
  { value: 'medium', label: 'متوسط' },
  { value: 'high',   label: 'بالا' },
];

export function ControlPanel() {
  const [open, setOpen] = useState(false);
  const store = useSimulatorStore();

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        style={{
          position: 'absolute',
          top: 20,
          left: 20,
          zIndex: 100,
          padding: '8px 16px',
          background: 'rgba(255, 255, 255, 0.15)',
          backdropFilter: 'blur(8px)',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          borderRadius: 6,
          color: 'white',
          cursor: 'pointer',
          fontSize: 14,
        }}
      >
        ⚙️ کنترل‌ها
      </button>

      <Drawer
        title="🎬 کنترل‌های شبیه‌ساز"
        placement="left"
        open={open}
        onClose={() => setOpen(false)}
        width={320}
      >
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={5}>آب و هوا</Title>
            <Segmented
              block
              options={WEATHER_OPTIONS}
              value={store.weather}
              onChange={(v) => store.setWeather(v as Weather)}
            />
          </div>

          <div>
            <Title level={5}>
              زمان روز
              <Text type="secondary" style={{ fontSize: 12, marginRight: 8 }}>
                {store.autoSunCycle && '(چرخه خودکار)'}
              </Text>
            </Title>
            <Segmented
              block
              options={TIME_OPTIONS}
              value={store.timeOfDay}
              onChange={(v) => store.setTimeOfDay(v as TimeOfDay)}
              disabled={store.autoSunCycle}
            />
            <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
              <Switch
                checked={store.autoSunCycle}
                onChange={store.toggleSunCycle}
              />
              <Text>چرخه خودکار خورشید</Text>
            </div>
          </div>

          <div>
            <Title level={5}>باد: {store.windSpeed} km/h</Title>
            <Slider
              min={0}
              max={80}
              value={store.windSpeed}
              onChange={store.setWindSpeed}
            />
          </div>

          <div>
            <Title level={5}>کیفیت رندر</Title>
            <Segmented
              block
              options={QUALITY_OPTIONS}
              value={store.quality}
              onChange={(v) => store.setQuality(v as any)}
            />
          </div>
        </Space>
      </Drawer>
    </>
  );
}
