import { type ReactNode } from 'react';
import { cn } from '@eco/utils';

export type WeatherCondition = 'sunny' | 'cloudy' | 'rainy' | 'snowy' | 'windy' | 'stormy';

export type WeatherData = {
  temperature: number;
  feelsLike: number;
  condition: WeatherCondition;
  humidity: number;
  windSpeed: number;
  location: string;
};

export type WeatherWidgetProps = {
  data?: WeatherData;
  className?: string;
  onRefresh?: () => void;
};

const WEATHER_ICONS: Record<WeatherCondition, ReactNode> = {
  sunny: <span className="text-4xl">☀️</span>,
  cloudy: <span className="text-4xl">☁️</span>,
  rainy: <span className="text-4xl">🌧️</span>,
  snowy: <span className="text-4xl">❄️</span>,
  windy: <span className="text-4xl">💨</span>,
  stormy: <span className="text-4xl">⛈️</span>,
};

export function WeatherWidget({ data, className, onRefresh }: WeatherWidgetProps) {
  const defaultData: WeatherData = {
    temperature: 22,
    feelsLike: 24,
    condition: 'sunny',
    humidity: 45,
    windSpeed: 12,
    location: 'تهران',
  };

  const weather = data ?? defaultData;

  return (
    <div className={cn('flex flex-col gap-4 rounded-lg border border-ink/10 bg-surface-raised p-5', className)}>
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-ink">{weather.location}</h3>
          <p className="text-xs text-ink-muted">آب و هوا</p>
        </div>
        {onRefresh && (
          <button
            type="button"
            onClick={onRefresh}
            className="rounded-md p-1 text-ink-muted hover:bg-surface-muted"
            aria-label="Refresh weather"
          >
            🔄
          </button>
        )}
      </div>

      <div className="flex items-center gap-4">
        <div className="flex-shrink-0">
          {WEATHER_ICONS[weather.condition]}
        </div>
        <div className="flex flex-col">
          <span className="text-4xl font-bold text-ink">{weather.temperature}°</span>
          <span className="text-xs text-ink-muted">احساس مانند {weather.feelsLike}°</span>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-ink-muted">
        <div className="flex items-center gap-1">
          <span>💧</span>
          <span>رطوبت {weather.humidity}%</span>
        </div>
        <div className="flex items-center gap-1">
          <span>🌬️</span>
          <span>باد {weather.windSpeed} km/h</span>
        </div>
      </div>
    </div>
  );
}
