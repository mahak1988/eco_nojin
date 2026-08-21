"use client";

import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";

export interface RainPoint {
  d: string;
  mm: number;
}

/** نمودار بارش روزانه (mm) — BarChart */
export function RainfallChart({ data }: { data: RainPoint[] }) {
  return (
    <div dir="ltr" className="w-full">
      <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="d" tick={{ fontSize: 10 }} />
        <YAxis tick={{ fontSize: 11 }} label={{ value: "mm", angle: -90, position: "insideLeft", fontSize: 11 }} />
        <Tooltip />
        <Bar dataKey="mm" name="بارش" fill="#6366f1" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
    </div>
  );
}
