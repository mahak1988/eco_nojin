/** IoT Device Panel — shows connected sensors and their real-time status. */

import { useState, useCallback } from 'react';
import { RefreshCw, Radio, AlertTriangle, CheckCircle, XCircle, Thermometer, Droplets, Cloud, MapPin, Activity } from 'lucide-react';
import { useBilingual } from '../../hooks/useBilingual';
import { getApiBase } from '../../lib/api';

interface Device {
  id: string;
  device_name: string;
  device_type: string;
  sensor_types: string[];
  location: Record<string, unknown>;
  status: 'active' | 'inactive' | 'error';
  firmware_version?: string;
  last_seen?: string;
}

interface DeviceReading {
  sensor_type: string;
  value: number;
  unit: string;
  qa_status: string;
  recorded_at?: string;
}

interface IoTDevicePanelProps {
  devices?: Device[];
  onRefresh?: () => void;
}

const SENSOR_ICONS: Record<string, React.ReactNode> = {
  soil_moisture: <Droplets className="h-4 w-4" />,
  temp: <Thermometer className="h-4 w-4" />,
  ec: <Activity className="h-4 w-4" />,
  flow: <Cloud className="h-4 w-4" />,
};

export default function IoTDevicePanel({ devices: propDevices, onRefresh }: IoTDevicePanelProps) {
  const { lang } = useBilingual();
  const [devices, setDevices] = useState(propDevices ?? []);
  const [readings, setReadings] = useState<Record<string, DeviceReading[]>>({});
  const [loading, setLoading] = useState(false);

  const fetchReadings = useCallback(async (deviceId: string) => {
    try {
      const res = await fetch(`${getApiBase()}/api/v1/iot/devices/${deviceId}/readings?limit=5`);
      if (res.ok) {
        const data = await res.json();
        setReadings((prev) => ({ ...prev, [deviceId]: data.readings ?? [] }));
      }
    } catch {
      /* ignore */
    }
  }, []);

  const handleRefresh = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${getApiBase()}/api/v1/iot/devices?limit=50`);
      if (res.ok) {
        const data = await res.json();
        setDevices(data.devices ?? []);
        for (const d of data.devices ?? []) {
          fetchReadings(d.id);
        }
      }
      onRefresh?.();
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, [fetchReadings, onRefresh]);

  const statusIcon = (status: string) => {
    if (status === 'active') return <CheckCircle className="h-3.5 w-3.5 text-green-400" />;
    if (status === 'error') return <XCircle className="h-3.5 w-3.5 text-red-400" />;
    return <AlertTriangle className="h-3.5 w-3.5 text-yellow-400" />;
  };

  const statusColor = (status: string) => {
    if (status === 'active') return 'bg-green-500';
    if (status === 'error') return 'bg-red-500';
    return 'bg-yellow-500';
  };

  const isFa = lang === 'fa';

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-extrabold text-[var(--color-night-100)] flex items-center gap-2">
          <Radio className="h-4 w-4 text-[var(--color-aqua-500)]" aria-hidden />
          {isFa ? 'دستگاه‌های IoT' : 'IoT Devices'}
        </h3>
        <button
          type="button"
          onClick={handleRefresh}
          disabled={loading}
          className="inline-flex items-center gap-1 text-[10px] font-bold text-[var(--color-night-200)]/50 hover:text-[var(--color-leaf-400)] disabled:opacity-50"
        >
          <RefreshCw className={`h-3 w-3 ${loading ? 'animate-spin' : ''}`} aria-hidden />
          {isFa ? 'بروزرسانی' : 'Refresh'}
        </button>
      </div>

      {devices.length === 0 ? (
        <div className="glass rounded-2xl p-6 text-center">
          <MapPin className="h-6 w-6 mx-auto mb-2 text-[var(--color-night-200)]/20" aria-hidden />
          <p className="text-xs text-[var(--color-night-200)]/50">
            {isFa ? 'هیچ دستگاهی ثبت نشده' : 'No devices registered'}
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {devices.map((device) => (
            <div
              key={device.id}
              className="glass rounded-xl p-3 hover:shadow-lg transition-shadow cursor-pointer"
              onClick={() => fetchReadings(device.id)}
            >
              <div className="flex items-center gap-2 mb-2">
                {statusIcon(device.status)}
                <span className={`text-[10px] font-bold ${statusColor(device.status)} rounded-full px-1.5 py-0.5 text-white`}>
                  {device.status}
                </span>
                <span className="text-xs font-extrabold text-[var(--color-night-100)] flex-1 truncate">
                  {device.device_name}
                </span>
              </div>

              <div className="flex flex-wrap gap-1 mb-2">
                {device.sensor_types.slice(0, 4).map((st) => (
                  <span
                    key={st}
                    className="inline-flex items-center gap-1 rounded-full bg-[var(--color-aqua-500)]/15 px-2 py-0.5 text-[10px] font-bold text-[var(--color-aqua-300)]"
                  >
                    {SENSOR_ICONS[st] ?? <Activity className="h-3 w-3" />}
                    {st.replace('_', ' ')}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between">
                <span className="text-[10px] text-[var(--color-night-200)]/40">
                  {device.firmware_version ? `v${device.firmware_version}` : ''}
                </span>
                {device.last_seen && (
                  <span className="text-[10px] text-[var(--color-night-200)]/40">
                    {isFa ? 'آخرین ارتباط' : 'Last seen'}: {new Date(device.last_seen).toLocaleString(isFa ? 'fa-IR' : 'en-US')}
                  </span>
                )}
              </div>

              {readings[device.id] && readings[device.id].length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1.5 border-t border-white/5 pt-2">
                  {readings[device.id].map((r, i) => (
                    <span key={i} className="text-[10px] text-[var(--color-night-200)]/60 dir-ltr" dir="ltr">
                      {r.sensor_type}: <strong>{r.value}</strong> {r.unit}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
