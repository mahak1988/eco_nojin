import {
  AreaChart as AreaChartRaw,
  Area as AreaRaw,
  XAxis as XAxisRaw,
  YAxis as YAxisRaw,
  CartesianGrid as CartesianGridRaw,
  Tooltip as TooltipRaw,
  ResponsiveContainer as ResponsiveContainerRaw,
  Legend as LegendRaw,
} from 'recharts';
import { useLang } from '../../i18n/LanguageContext';
import type { DataPoint } from './EcoChart';

const AreaChart = AreaChartRaw as any;
const Area = AreaRaw as any;
const XAxis = XAxisRaw as any;
const YAxis = YAxisRaw as any;
const CartesianGrid = CartesianGridRaw as any;
const Tooltip = TooltipRaw as any;
const ResponsiveContainer = ResponsiveContainerRaw as any;
const Legend = LegendRaw as any;

interface RechartsChartProps {
  data: DataPoint[];
  title?: string;
  color?: string;
  height?: number;
}

export function RechartsChart({
  data,
  title,
  color = '#2fb36b',
  height = 300,
}: RechartsChartProps) {
  const { lang } = useLang();

  if (data.length === 0) {
    return null;
  }

  return (
    <div className="w-full" style={{ height }}>
      {title ? (
        <h3 className="mb-4 text-sm font-extrabold text-[var(--color-night-100)]">
          {title}
        </h3>
      ) : null}
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="4 4" stroke="rgba(255,255,255,0.08)" />
          <XAxis
            dataKey="label"
            tick={{ fill: 'var(--color-night-200)', fontSize: 10 }}
            angle={-30}
            textAnchor="end"
            height={40}
          />
          <YAxis tick={{ fill: 'var(--color-night-200)', fontSize: 10 }} />
          <Tooltip
            contentStyle={{
              background: 'var(--color-night-900)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              color: 'var(--color-night-100)',
            }}
          />
          {data.some((d) => d.secondary !== undefined) ? (
            <Legend />
          ) : null}
          <Area
            type="monotone"
            dataKey="value"
            stroke={color}
            strokeWidth={2}
            fill={`url(#grad-${color.replace('#', '')})`}
            strokeLinecap="round"
            strokeLinejoin="round"
            name={lang === 'fa' ? 'مقدار اصلی' : 'Main Value'}
          />
          {data.some((d) => d.secondary !== undefined) ? (
            <Area
              type="monotone"
              dataKey="secondary"
              stroke="#45bcd4"
              strokeWidth={2}
              strokeDasharray="6 4"
              strokeLinecap="round"
              fill="none"
              name={lang === 'fa' ? 'مقدار فرعی' : 'Secondary'}
            />
          ) : null}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
