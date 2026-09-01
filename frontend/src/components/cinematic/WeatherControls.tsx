import { useWeatherStore, WeatherCondition, TimeOfDay } from '../../hooks/useWeatherStore';
import { Card, Slider, Select, Button, Space, Typography, Switch, Row, Col } from 'antd';
import {
  CloudOutlined,
  CloudRainOutlined,
  CloudSnowOutlined,
  CloudOutlined as DustOutlined,
  SunOutlined,
  MoonOutlined,
  ThunderboltOutlined,
  WindOutlined,
  ThermometerOutlined,
  ExperimentOutlined,
} from '@ant-design/icons';

const { Title, Text } = Typography;

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

  return (
    <Card
      title="🎬 کنترل سینمایی شبیه‌ساز"
      style={{
        position: 'absolute',
        top: 20,
        right: 20,
        width: 360,
        background: 'rgba(20, 20, 30, 0.85)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.1)',
        color: 'white',
        zIndex: 1000,
      }}
      styles={{
        header: { borderBottom: '1px solid rgba(255,255,255,0.1)', color: 'white' },
        body: { color: 'white' },
      }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        {/* Weather Condition */}
        <div>
          <Text strong style={{ color: '#aaa' }}>آب و هوا</Text>
          <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
            {conditions.map((c) => (
              <Col key={c.value} span={8}>
                <Button
                  type={store.condition === c.value ? 'primary' : 'default'}
                  icon={c.icon}
                  onClick={() => store.setCondition(c.value)}
                  block
                  size="small"
                >
                  {c.label}
                </Button>
              </Col>
            ))}
          </Row>
        </div>

        {/* Time of Day */}
        <div>
          <Text strong style={{ color: '#aaa' }}>زمان روز</Text>
          <Row gutter={[8, 8]} style={{ marginTop: 8 }}>
            {times.map((t) => (
              <Col key={t.value} span={6}>
                <Button
                  type={store.timeOfDay === t.value ? 'primary' : 'default'}
                  icon={t.icon}
                  onClick={() => store.setTimeOfDay(t.value)}
                  block
                  size="small"
                >
                  {t.label}
                </Button>
              </Col>
            ))}
          </Row>
        </div>

        {/* Wind */}
        <div>
          <Text strong style={{ color: '#aaa' }}>
            <WindOutlined /> باد: {store.windSpeed} km/h
          </Text>
          <Slider
            min={0}
            max={100}
            value={store.windSpeed}
            onChange={(v) => store.setWind(v, store.windDirection)}
          />
        </div>

        {/* Intensity */}
        <div>
          <Text strong style={{ color: '#aaa' }}>شدت: {Math.round(store.intensity * 100)}%</Text>
          <Slider
            min={0}
            max={100}
            value={store.intensity * 100}
            onChange={(v) => store.setIntensity(v / 100)}
          />
        </div>

        {/* Plant Growth */}
        <div>
          <Text strong style={{ color: '#aaa' }}>
            <ExperimentOutlined /> رشد گیاه: {Math.round(store.plantGrowthStage * 100)}%
          </Text>
          <Slider
            min={0}
            max={100}
            value={store.plantGrowthStage * 100}
            onChange={(v) => store.setPlantGrowth(v / 100)}
          />
        </div>

        {/* Temperature */}
        <div>
          <Text strong style={{ color: '#aaa' }}>
            <ThermometerOutlined /> دما: {store.temperature}°C
          </Text>
          <Slider
            min={-20}
            max={50}
            value={store.temperature}
            onChange={(v) => store.setTemperature(v)}
          />
        </div>

        {/* Fog */}
        <div>
          <Text strong style={{ color: '#aaa' }}>تراکم مه: {Math.round(store.fogDensity * 100)}%</Text>
          <Slider
            min={0}
            max={100}
            value={store.fogDensity * 100}
            onChange={(v) => store.setFogDensity(v / 100)}
          />
        </div>

        {/* Post Processing Toggle */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Text strong style={{ color: '#aaa' }}>جلوه‌های سینمایی</Text>
          <Switch checked={store.enablePostProcessing} onChange={store.togglePostProcessing} />
        </div>
      </Space>
    </Card>
  );
}
