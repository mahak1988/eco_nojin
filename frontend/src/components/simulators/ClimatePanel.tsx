import { useState, memo, useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Sun,
  Cloud,
  CloudRain,
  CloudSnow,
  Droplets,
  Wind,
  Thermometer,
  Clock,
  Calendar,
} from 'lucide-react';

export type TimeScale = 'hour' | 'day' | 'week' | 'month';

export interface ClimateState {
  timeScale: TimeScale;
  timeIndex: number; // 0-23 for hour, 0-364 for day, 0-51 for week, 0-11 for month
  playing: boolean;
  temperature: number; // °C
  humidity: number; // %
  precipitation: number; // mm
  precipType: 'none' | 'rain' | 'snow';
  windSpeed: number; // km/h
  windDirection: number; // degrees
  solarAngle: number; // degrees
  isDaytime: boolean;
  droughtIndex: number; // 0-1
}

interface Props {
  state: ClimateState;
  onChange: (state: ClimateState) => void;
  latitude?: number;
}

// Solar angle calculation (astronomical)
function calcSolarAngle(hour: number, dayOfYear: number, lat = 35.5): number {
  const declination = 23.45 * Math.sin((2 * Math.PI * (284 + dayOfYear)) / 365);
  const hourAngle = (hour - 12) * 15;
  const latRad = (lat * Math.PI) / 180;
  const decRad = (declination * Math.PI) / 180;
  const hRad = (hourAngle * Math.PI) / 180;
  const sinAlt =
    Math.sin(latRad) * Math.sin(decRad) + Math.cos(latRad) * Math.cos(decRad) * Math.cos(hRad);
  return (Math.asin(Math.max(-1, Math.min(1, sinAlt))) * 180) / Math.PI;
}

function calcPrecipType(temp: number, humidity: number): 'none' | 'rain' | 'snow' {
  if (humidity < 0.6) return 'none';
  return temp < 2 ? 'snow' : 'rain';
}

export const ClimatePanel = memo(function ClimatePanel({
  state,
  onChange,
  latitude = 35.5,
}: Props) {
  const { i18n } = useTranslation();
  const isFa = i18n.language === 'fa';

  const update = (patch: Partial<ClimateState>) => {
    onChange({ ...state, ...patch });
  };

  // Recompute derived values
  const dayOfYear = useMemo(() => {
    if (state.timeScale === 'hour') return Math.floor(state.timeIndex / 24) + 1;
    if (state.timeScale === 'day') return state.timeIndex + 1;
    if (state.timeScale === 'week') return state.timeIndex * 7 + 1;
    return state.timeIndex * 30 + 15;
  }, [state.timeScale, state.timeIndex]);

  const hour = useMemo(() => {
    if (state.timeScale === 'hour') return state.timeIndex % 24;
    return 12; // noon for other scales
  }, [state.timeScale, state.timeIndex]);

  const solarAngle = calcSolarAngle(hour, dayOfYear, latitude);
  const isDaytime = solarAngle > 0;
  const precipType = calcPrecipType(state.temperature, state.humidity);

  const scales: Array<{ value: TimeScale; icon: any; label: string; fa: string; max: number }> = [
    { value: 'hour', icon: Clock, label: 'Hourly', fa: 'ساعتی', max: 23 },
    { value: 'day', icon: Calendar, label: 'Daily', fa: 'روزانه', max: 364 },
    { value: 'week', icon: Calendar, label: 'Weekly', fa: 'هفتگی', max: 51 },
    { value: 'month', icon: Calendar, label: 'Monthly', fa: 'ماهانه', max: 11 },
  ];

  const cardStyle = {
    background: 'rgba(0,0,0,0.5)',
    backdropFilter: 'blur(15px)',
    padding: '12px',
    borderRadius: '12px',
    border: '1px solid rgba(255,255,255,0.1)',
    marginBottom: '10px',
  };

  const rowStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '6px 0',
    fontSize: '12px',
  };

  return (
    <div style={{ width: '100%', fontFamily: 'var(--font-persian, var(--font-latin))' }}>
      {/* Time Scale Selector */}
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
          {isFa ? 'مقیاس زمانی' : 'Time Scale'}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '4px' }}>
          {scales.map((s) => {
            const Icon = s.icon;
            const active = state.timeScale === s.value;
            return (
              <button
                key={s.value}
                onClick={() => update({ timeScale: s.value, timeIndex: 0 })}
                style={{
                  padding: '8px 4px',
                  borderRadius: '8px',
                  background: active ? '#3b82f6' : 'rgba(255,255,255,0.05)',
                  color: active ? 'white' : 'rgba(255,255,255,0.7)',
                  border: active ? 'none' : '1px solid rgba(255,255,255,0.1)',
                  cursor: 'pointer',
                  fontSize: '11px',
                  fontWeight: 600,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '2px',
                }}
              >
                <Icon size={14} />
                <span>{isFa ? s.fa : s.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Time Slider */}
      <div style={cardStyle}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '11px',
            marginBottom: '6px',
          }}
        >
          <span style={{ color: 'rgba(255,255,255,0.6)' }}>{isFa ? 'زمان' : 'Time'}</span>
          <span style={{ color: '#3b82f6', fontWeight: 700 }}>
            {state.timeScale === 'hour' && `${state.timeIndex}:00`}
            {state.timeScale === 'day' && `${isFa ? 'روز' : 'Day'} ${state.timeIndex + 1}/365`}
            {state.timeScale === 'week' && `${isFa ? 'هفته' : 'Week'} ${state.timeIndex + 1}/52`}
            {state.timeScale === 'month' &&
              (isFa
                ? [
                    'فروردین',
                    'اردیبهشت',
                    'خرداد',
                    'تیر',
                    'مرداد',
                    'شهریور',
                    'مهر',
                    'آبان',
                    'آذر',
                    'دی',
                    'بهمن',
                    'اسفند',
                  ][state.timeIndex]
                : [
                    'Jan',
                    'Feb',
                    'Mar',
                    'Apr',
                    'May',
                    'Jun',
                    'Jul',
                    'Aug',
                    'Sep',
                    'Oct',
                    'Nov',
                    'Dec',
                  ][state.timeIndex])}
          </span>
        </div>
        <input
          type="range"
          min={0}
          max={scales.find((s) => s.value === state.timeScale)?.max || 11}
          value={state.timeIndex}
          onChange={(e) => update({ timeIndex: parseInt(e.target.value) })}
          style={{ width: '100%', accentColor: '#3b82f6' }}
        />
      </div>

      {/* Sun/Night indicator */}
      <div
        style={{
          ...cardStyle,
          background: isDaytime
            ? 'linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.1))'
            : 'linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.8))',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: isDaytime
                ? 'radial-gradient(circle, #fbbf24, #f59e0b)'
                : 'radial-gradient(circle, #64748b, #1e293b)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: isDaytime ? '0 0 20px #fbbf24' : '0 0 10px #64748b',
            }}
          >
            <Sun size={20} color={isDaytime ? 'white' : '#94a3b8'} />
          </div>
          <div>
            <div style={{ fontSize: '14px', fontWeight: 700, color: 'white' }}>
              {isDaytime ? (isFa ? 'روز' : 'Daytime') : isFa ? 'شب' : 'Night'}
            </div>
            <div style={{ fontSize: '11px', color: 'rgba(255,255,255,0.6)' }}>
              {isFa ? 'زاویه خورشید' : 'Solar Angle'}: {solarAngle.toFixed(1)}°
            </div>
          </div>
        </div>
      </div>

      {/* Climate Metrics */}
      <div style={cardStyle}>
        <div style={rowStyle}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444' }}>
            <Thermometer size={14} /> {isFa ? 'دما' : 'Temp'}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'white', fontWeight: 700 }}>
              {state.temperature.toFixed(1)}°C
            </span>
            <input
              type="range"
              min={-10}
              max={45}
              step={0.5}
              value={state.temperature}
              onChange={(e) => update({ temperature: parseFloat(e.target.value) })}
              style={{ width: '80px', accentColor: '#ef4444' }}
            />
          </div>
        </div>

        <div style={rowStyle}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#06b6d4' }}>
            <Droplets size={14} /> {isFa ? 'رطوبت' : 'Humidity'}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'white', fontWeight: 700 }}>
              {(state.humidity * 100).toFixed(0)}%
            </span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={state.humidity}
              onChange={(e) => update({ humidity: parseFloat(e.target.value) })}
              style={{ width: '80px', accentColor: '#06b6d4' }}
            />
          </div>
        </div>

        <div style={rowStyle}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#3b82f6' }}>
            {precipType === 'snow' ? (
              <CloudSnow size={14} />
            ) : precipType === 'rain' ? (
              <CloudRain size={14} />
            ) : (
              <Cloud size={14} />
            )}
            {isFa ? 'بارش' : 'Precip'}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'white', fontWeight: 700 }}>
              {state.precipitation.toFixed(1)}mm
              {precipType === 'snow' ? ' ❄️' : precipType === 'rain' ? ' 🌧️' : ''}
            </span>
            <input
              type="range"
              min={0}
              max={50}
              step={0.5}
              value={state.precipitation}
              onChange={(e) => update({ precipitation: parseFloat(e.target.value) })}
              style={{ width: '80px', accentColor: '#3b82f6' }}
            />
          </div>
        </div>

        <div style={rowStyle}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#a855f7' }}>
            <Wind size={14} /> {isFa ? 'باد' : 'Wind'}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'white', fontWeight: 700 }}>
              {state.windSpeed.toFixed(0)}km/h
            </span>
            <input
              type="range"
              min={0}
              max={100}
              step={1}
              value={state.windSpeed}
              onChange={(e) => update({ windSpeed: parseFloat(e.target.value) })}
              style={{ width: '80px', accentColor: '#a855f7' }}
            />
          </div>
        </div>

        <div style={rowStyle}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#14b8a6' }}>
            🧭 {isFa ? 'جهت باد' : 'Direction'}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'white', fontWeight: 700, minWidth: '30px' }}>
              {state.windDirection.toFixed(0)}°
            </span>
            <input
              type="range"
              min={0}
              max={360}
              step={5}
              value={state.windDirection}
              onChange={(e) => update({ windDirection: parseFloat(e.target.value) })}
              style={{ width: '80px', accentColor: '#14b8a6' }}
            />
          </div>
        </div>

        <div style={rowStyle}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f59e0b' }}>
            🏜️ {isFa ? 'شاخص خشکسالی' : 'Drought'}
          </span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ color: 'white', fontWeight: 700 }}>
              {(state.droughtIndex * 100).toFixed(0)}%
            </span>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={state.droughtIndex}
              onChange={(e) => update({ droughtIndex: parseFloat(e.target.value) })}
              style={{ width: '80px', accentColor: '#f59e0b' }}
            />
          </div>
        </div>
      </div>

      {/* Wind direction compass */}
      <div style={cardStyle}>
        <div
          style={{
            fontSize: '11px',
            color: 'rgba(255,255,255,0.6)',
            marginBottom: '8px',
            textAlign: 'center',
          }}
        >
          {isFa ? 'جهت باد' : 'Wind Direction'}
        </div>
        <div style={{ position: 'relative', width: '80px', height: '80px', margin: '0 auto' }}>
          <svg width="80" height="80" viewBox="0 0 80 80">
            <circle
              cx="40"
              cy="40"
              r="35"
              fill="rgba(255,255,255,0.05)"
              stroke="rgba(255,255,255,0.2)"
              strokeWidth="1"
            />
            <text x="40" y="8" textAnchor="middle" fill="white" fontSize="10">
              N
            </text>
            <text x="75" y="43" textAnchor="middle" fill="white" fontSize="10">
              E
            </text>
            <text x="40" y="78" textAnchor="middle" fill="white" fontSize="10">
              S
            </text>
            <text x="5" y="43" textAnchor="middle" fill="white" fontSize="10">
              W
            </text>
            <g transform={`rotate(${state.windDirection}, 40, 40)`}>
              <polygon points="40,15 35,40 40,35 45,40" fill="#3b82f6" />
            </g>
          </svg>
        </div>
      </div>
    </div>
  );
});

export const defaultClimate: ClimateState = {
  timeScale: 'month',
  timeIndex: 5,
  playing: false,
  temperature: 22,
  humidity: 0.5,
  precipitation: 5,
  precipType: 'none',
  windSpeed: 15,
  windDirection: 180,
  solarAngle: 45,
  isDaytime: true,
  droughtIndex: 0.3,
};
