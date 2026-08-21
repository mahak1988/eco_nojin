"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";

export interface MoisturePoint {
  t: string;
  theta: number;
  fc?: number;
  pwp?: number;
}

/** رطوبت خاک (θ) با خطوط ظرفیت مزرعه (FC) و نقطه پژمردگی (PWP) */
export function SoilMoistureChart({ data, unit = "m³/m³" }: { data: MoisturePoint[]; unit?: string }) {
  return (
    <div dir="ltr" className="w-full">
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis dataKey="t" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} label={{ value: unit, angle: -90, position: "insideLeft", fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="theta" name="رطوبت" stroke="#0ea5e9" strokeWidth={2} dot={false} />
          {data.some((d) => d.fc !== undefined) && (
            <Line type="monotone" dataKey="fc" name="ظرفیت مزرعه" stroke="#10b981" strokeWidth={1.5} strokeDasharray="5 4" dot={false} />
          )}
          {data.some((d) => d.pwp !== undefined) && (
            <Line type="monotone" dataKey="pwp" name="نقطه پژمردگی" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="3 4" dot={false} />
          )}
          <ReferenceLine y={0.3} stroke="#94a3b8" strokeDasharray="4 4" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
