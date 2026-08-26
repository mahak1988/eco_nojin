import React from 'react';
import { Card } from '../ui';
import { CloudRain, Wind, Thermometer, Sun } from 'lucide-react';

interface Weather {
  rainfall: number;
  wind: number;
  temperature: number;
  sunIntensity: number;
}

interface VLLWeatherControlProps {
  weather: Weather;
  onChange: (weather: Weather) => void;
}

export const VLLWeatherControl: React.FC<VLLWeatherControlProps> = ({ weather, onChange }) => {
  return (
    <Card title="☁️ کنترل آب و هوا" icon={<CloudRain size={18} />} className="mb-4">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {/* Rainfall */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <CloudRain size={14} color="#3b82f6" /> بارش
            </span>
            <strong>{weather.rainfall} mm/hr</strong>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={weather.rainfall}
            onChange={(e) => onChange({ ...weather, rainfall: parseInt(e.target.value) })}
            style={{ width: '100%' }}
          />
        </div>

        {/* Wind */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Wind size={14} color="#a3a3a3" /> سرعت باد
            </span>
            <strong>{weather.wind} m/s</strong>
          </div>
          <input
            type="range"
            min="0"
            max="30"
            value={weather.wind}
            onChange={(e) => onChange({ ...weather, wind: parseInt(e.target.value) })}
            style={{ width: '100%' }}
          />
        </div>

        {/* Temperature */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Thermometer size={14} color="#ef4444" /> دما
            </span>
            <strong>{weather.temperature}°C</strong>
          </div>
          <input
            type="range"
            min="-10"
            max="50"
            value={weather.temperature}
            onChange={(e) => onChange({ ...weather, temperature: parseInt(e.target.value) })}
            style={{ width: '100%' }}
          />
        </div>

        {/* Sun Intensity */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem', marginBottom: '0.25rem' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Sun size={14} color="#fbbf24" /> تابش خورشید
            </span>
            <strong>{(weather.sunIntensity * 100).toFixed(0)}٪</strong>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={weather.sunIntensity * 100}
            onChange={(e) => onChange({ ...weather, sunIntensity: parseInt(e.target.value) / 100 })}
            style={{ width: '100%' }}
          />
        </div>
      </div>
    </Card>
  );
};
