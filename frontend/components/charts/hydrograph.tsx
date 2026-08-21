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
} from "recharts";

export interface FlowPoint {
  t: string;
  q: number;
  p?: number;
}

/** هیدروگراف: دبی (m3/s) نسبت به زمان — نمودار علمی استاندارد هیدرولوژی */
export function Hydrograph({ data, unit = "m³/s" }: { data: FlowPoint[]; unit?: string }) {
  return (
    <div dir="ltr" className="w-full">
      <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="t" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} label={{ value: unit, angle: -90, position: "insideLeft", fontSize: 11 }} />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="q" name="دبی" stroke="#0ea5e9" strokeWidth={2} dot={false} />
        {data.some((d) => d.p !== undefined) ? (
          <Line type="monotone" dataKey="p" name="بارش (mm)" stroke="#8b5cf6" strokeWidth={1.5} dot={false} />
        ) : null}
      </LineChart>
    </ResponsiveContainer>
    </div>
  );
}
