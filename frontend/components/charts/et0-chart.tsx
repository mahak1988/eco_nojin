"use client";

import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";

export interface Et0Point {
  d: string;
  et0: number;
}

/** تبخیر و تعرق مرجع (ET0) — نمودار ناحیه‌ای با گرادیان */
export function Et0Chart({ data, unit = "mm/day" }: { data: Et0Point[]; unit?: string }) {
  return (
    <div dir="ltr" className="w-full">
      <ResponsiveContainer width="100%" height={240}>
        <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="et0Fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0ea5e9" stopOpacity={0.35} />
              <stop offset="100%" stopColor="#0ea5e9" stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis dataKey="d" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} label={{ value: unit, angle: -90, position: "insideLeft", fontSize: 11 }} />
          <Tooltip />
          <Area type="monotone" dataKey="et0" name="ET0" stroke="#0284c7" strokeWidth={2} fill="url(#et0Fill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
