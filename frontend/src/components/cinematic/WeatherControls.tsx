import { useWeatherStore, WeatherCondition, TimeOfDay } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';
import { Card, Slider, Button, Space, Typography, Row, Col, Divider } from 'antd';
import { useState } from 'react';

const { Text } = Typography;

const conditions: { value: WeatherCondition; label: string; emoji: string }[] = [
  { value: 'clear', label: 'آفتابی', emoji: '☀️' },
  { value: 'rain', label: 'باران', emoji: '🌧️' },
  { value: 'snow', label: 'برف', emoji: '❄️' },
  { value: 'dust', label: 'ریزگرد', emoji: '🌫️' },
  { value: 'drought', label: 'خشکسالی', emoji: '🏜️' },
  { value: 'storm', label: 'طوفان', emoji: '⛈️' },
];

const times: { value: TimeOfDay; label: string; emoji: string }[] = [
  { value: 'dawn', label: 'طلوع', emoji: '🌅' },
  { value: 'day', label: 'روز', emoji: '☀️' },
  { value: 'dusk', label: 'غروب', emoji: '🌇' },
  { value: 'night', label: 'شب', emoji: '🌙' },
];

const agriculturalFeatures = [
  { key: 'enableInsects', label: 'حشرات', emoji: '🐝' },
  { key: 'enableDomesticAnimals', label: 'دام', emoji: '🐄' },
  { key: 'enablePoultry', label: 'طیور', emoji: '🐔' },
  { key: 'enableFlood', label: 'سیلاب', emoji: '🌊' },
  { key: 'enableIrrigation', label: 'آبیاری', emoji: '💧' },
  { key: 'enableWell', label: 'چاه', emoji: '⛲' },
  { key: 'enableRiver', label: 'رودخانه', emoji: '🏞️' },
  { key: 'enableCoastline', label: 'ساحل', emoji: '🏖️' },
  { key: 'enableWatershed', label: 'آبخیزداری', emoji: '🏗️' },
  { key: 'enablePlowing', label: 'شخم‌زنی', emoji: '🚜' },
];

const artisticEffects = [
  { key: 'enableSunCycle', label: 'حرکت خورشید', emoji: '🌞' },
  { key: 'enableAurora', label: 'شفق قطبی', emoji: '🌌' },
  { key: 'enableRainbow', label: 'رنگین‌کمان', emoji: '🌈' },
  { key: 'enableFireflies', label: 'کرم شب‌تاب', emoji: '✨' },
  { key: 'enableBirds', label: 'پرندگان', emoji: '🦅' },
  { key: 'enableButterflies', label: 'پروانه', emoji: '🦋' },
  { key: 'enableLetterbox', label: 'لترباکس', emoji: '🎬' },
  { key: 'enableFilmGrain', label: 'گرین فیلم', emoji: '📽️' },
];

export function WeatherControls() {
  const store = useWeatherStore();
  const a = useArtisticStore();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <Card
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>🎬 کنترل سینمایی</span>
          <Button type="text" size="small" onClick={() => setCollapsed(!collapsed)}>
            {collapsed ? '▼' : '▲'}
          </Button>
        </div>
      }
      style={{
        position: 'absolute', top: 20, right: 20, width: 380,
        maxHeight: 'calc(100vh - 40px)', overflowY: 'auto',
        background: 'rgba(20, 20, 30, 0.9)', backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)', color: 'white', zIndex: 1000,
      }}
      styles={{
        header: { borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'white' },
        body: { color: 'white', padding: collapsed ? 0 : 16 },
      }}
    >
      {!collapsed && (
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <div>
            <Text strong style={{ color: '#aaa' }}>🌤️ آب و هوا</Text>
            <Row gutter={[6, 6]} style={{ marginTop: 6 }}>
              {conditions.map((c) => (
                <Col key={c.value} span={8}>
                  <Button
                    type={store.condition === c.value ? 'primary' : 'default'}
                    onClick={() => store.setCondition(c.value)}
                    block size="small" style={{ fontSize: 13 }}
                  >{c.emoji} {c.label}</Button>
                </Col>
              ))}
            </Row>
          </div>

          <div>
            <Text strong style={{ color: '#aaa' }}>⏰ زمان روز</Text>
            <Row gutter={[6, 6]} style={{ marginTop: 6 }}>
              {times.map((t) => (
                <Col key={t.value} span={6}>
                  <Button
                    type={store.timeOfDay === t.value ? 'primary' : 'default'}
                    onClick={() => store.setTimeOfDay(t.value)}
                    block size="small"
                  >{t.emoji} {t.label}</Button>
                </Col>
              ))}
            </Row>
          </div>

          <div>
            <Text strong style={{ color: '#aaa' }}>💨 باد: {store.windSpeed} km/h</Text>
            <Slider min={0} max={100} value={store.windSpeed}
              onChange={(v) => store.setWind(v, store.windDirection)} />
          </div>

          <div>
            <Text strong style={{ color: '#aaa' }}>🌱 رشد گیاه: {Math.round(store.plantGrowthStage * 100)}%</Text>
            <Slider min={0} max={100} value={store.plantGrowthStage * 100}
              onChange={(v) => store.setPlantGrowth(v / 100)} />
          </div>

          <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />

          <div>
            <Text strong style={{ color: '#feca57', fontSize: 13 }}>🌾 اکوسیستم کشاورزی</Text>
            <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
              {agriculturalFeatures.map(({ key, label, emoji }) => (
                <Col key={key} span={12}>
                  <Button
                    type={(a as any)[key] ? 'primary' : 'default'}
                    onClick={() => a.toggle(key)} block size="small"
                    style={{ textAlign: 'right' }}
                  >{emoji} {label}</Button>
                </Col>
              ))}
            </Row>
          </div>

          <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />

          <div>
            <Text strong style={{ color: '#feca57', fontSize: 13 }}>✨ جلوه‌های هنری</Text>
            <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
              {artisticEffects.map(({ key, label, emoji }) => (
                <Col key={key} span={12}>
                  <Button
                    type={(a as any)[key] ? 'primary' : 'default'}
                    onClick={() => a.toggle(key)} block size="small"
                  >{emoji} {label}</Button>
                </Col>
              ))}
            </Row>
          </div>
        </Space>
      )}
    </Card>
  );
}
