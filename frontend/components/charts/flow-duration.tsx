"use client";

import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from "recharts";

export interface FlowDurationPoint {
  exceed: number;
  q: number;
}

/** منحنی تداوم جریان (FDC) — دبی نسبت به درصد تجاوز */
export function FlowDurationCurve({ data, unit = "m³/s" }: { data: FlowDurationPoint[]; unit?: string }) {
  return (
    <div dir="ltr" className="w-full">
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis
            dataKey="exceed"
            tick={{ fontSize: 11 }}
            label={{ value: "درصد تجاوز (%)", position: "insideBottom", offset: -4, fontSize: 11 }}
            type="number"
            domain={[0, 100]}
          />
          <YAxis
            tick={{ fontSize: 11 }}
            label={{ value: unit, angle: -90, position: "insideLeft", fontSize: 11 }}
            scale="log"
            domain={["auto", "auto"]}
            allowDataOverflow
          />
          <Tooltip />
          <Line type="monotone" dataKey="q" name="دبی" stroke="#8b5cf6" strokeWidth={2} dot={false} />
          <ReferenceLine x={95} stroke="#94a3b8" strokeDasharray="4 4" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
