import { useWeatherStore, WeatherCondition, TimeOfDay } from '../../hooks/useWeatherStore';
import { useArtisticStore } from '../../hooks/useArtisticStore';
import { Card, Slider, Button, Space, Typography, Switch, Row, Col, Divider } from 'antd';
import {
  CloudOutlined, CloudRainOutlined, CloudSnowOutlined,
  SunOutlined, MoonOutlined, ThunderboltOutlined, WindOutlined,
  ExperimentOutlined, BugOutlined, CowOutlined, BirdOutlined,
  ThunderboltOutlined as FloodIcon, ApiOutlined,
  BankOutlined, BranchesOutlined, FieldTimeOutlined,
} from '@ant-design/icons';
import { useState } from 'react';

const { Text } = Typography;

const conditions: { value: WeatherCondition; label: string; icon: any }[] = [
  { value: 'clear', label: 'آفتابی', icon: <SunOutlined /> },
  { value: 'rain', label: 'باران', icon: <CloudRainOutlined /> },
  { value: 'snow', label: 'برف', icon: <CloudSnowOutlined /> },
  { value: 'dust', label: 'ریزگرد', icon: <CloudOutlined /> },
  { value: 'drought', label: 'خشکسالی', icon: <SunOutlined /> },
  { value: 'storm', label: 'طوفان', icon: <ThunderboltOutlined /> },
];

const times: { value: TimeOfDay; label: string; icon: any }[] = [
  { value: 'dawn', label: 'طلوع', icon: <SunOutlined /> },
  { value: 'day', label: 'روز', icon: <SunOutlined /> },
  { value: 'dusk', label: 'غروب', icon: <SunOutlined /> },
  { value: 'night', label: 'شب', icon: <MoonOutlined /> },
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
            <Text strong style={{ color: '#aaa' }}>آب و هوا</Text>
            <Row gutter={[6, 6]} style={{ marginTop: 6 }}>
              {conditions.map((c) => (
                <Col key={c.value} span={8}>
                  <Button
                    type={store.condition === c.value ? 'primary' : 'default'}
                    icon={c.icon} onClick={() => store.setCondition(c.value)} block size="small"
                  >{c.label}</Button>
                </Col>
              ))}
            </Row>
          </div>

          <div>
            <Text strong style={{ color: '#aaa' }}>زمان روز</Text>
            <Row gutter={[6, 6]} style={{ marginTop: 6 }}>
              {times.map((t) => (
                <Col key={t.value} span={6}>
                  <Button
                    type={store.timeOfDay === t.value ? 'primary' : 'default'}
                    icon={t.icon} onClick={() => store.setTimeOfDay(t.value)} block size="small"
                  >{t.label}</Button>
                </Col>
              ))}
            </Row>
          </div>

          <div>
            <Text strong style={{ color: '#aaa' }}><WindOutlined /> باد: {store.windSpeed} km/h</Text>
            <Slider min={0} max={100} value={store.windSpeed}
              onChange={(v) => store.setWind(v, store.windDirection)} />
          </div>

          <div>
            <Text strong style={{ color: '#aaa' }}><ExperimentOutlined /> رشد گیاه: {Math.round(store.plantGrowthStage * 100)}%</Text>
            <Slider min={0} max={100} value={store.plantGrowthStage * 100}
              onChange={(v) => store.setPlantGrowth(v / 100)} />
          </div>

          <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />

          <div>
            <Text strong style={{ color: '#feca57', fontSize: 13 }}>🌾 اکوسیستم کشاورزی</Text>
            <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
              {[
                { key: 'enableInsects', label: 'حشرات', icon: <BugOutlined /> },
                { key: 'enableDomesticAnimals', label: 'دام', icon: <span>🐄</span> },
                { key: 'enablePoultry', label: 'طیور', icon: <span>🐔</span> },
                { key: 'enableFlood', label: 'سیلاب', icon: <span>🌊</span> },
                { key: 'enableIrrigation', label: 'آبیاری', icon: <span>💧</span> },
                { key: 'enableWell', label: 'چاه', icon: <span>⛲</span> },
                { key: 'enableRiver', label: 'رودخانه', icon: <span>🏞️</span> },
                { key: 'enableCoastline', label: 'ساحل', icon: <span>🏖️</span> },
                { key: 'enableWatershed', label: 'آبخیزداری', icon: <span>🏗️</span> },
                { key: 'enablePlowing', label: 'شخم‌زنی', icon: <span>🚜</span> },
              ].map(({ key, label, icon }) => (
                <Col key={key} span={12}>
                  <Button
                    type={(a as any)[key] ? 'primary' : 'default'}
                    onClick={() => a.toggle(key)} block size="small"
                    style={{ textAlign: 'right' }}
                  >{icon} {label}</Button>
                </Col>
              ))}
            </Row>
          </div>

          <Divider style={{ borderColor: 'rgba(255,255,255,0.1)', margin: '8px 0' }} />

          <div>
            <Text strong style={{ color: '#feca57', fontSize: 13 }}>✨ جلوه‌های هنری</Text>
            <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
              {[
                { key: 'enableAurora', label: 'شفق قطبی' },
                { key: 'enableRainbow', label: 'رنگین‌کمان' },
                { key: 'enableFireflies', label: 'کرم شب‌تاب' },
                { key: 'enableBirds', label: 'پرندگان' },
                { key: 'enableButterflies', label: 'پروانه' },
                { key: 'enableGodRays', label: 'پرتو خورشید' },
                { key: 'enableLetterbox', label: 'لترباکس' },
                { key: 'enableFilmGrain', label: 'گرین فیلم' },
              ].map(({ key, label }) => (
                <Col key={key} span={12}>
                  <Button
                    type={(a as any)[key] ? 'primary' : 'default'}
                    onClick={() => a.toggle(key)} block size="small"
                  >{label}</Button>
                </Col>
              ))}
            </Row>
          </div>
        </Space>
      )}
    </Card>
  );
}
