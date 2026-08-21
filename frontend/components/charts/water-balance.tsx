"use client";

import { ResponsiveContainer, ComposedChart, Bar, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

export interface BalancePoint {
  t: string;
  inflow: number;
  outflow: number;
  storage: number;
}

/** تراز آبی: ورودی (بارش) / خروجی (رواناب+تبخیر) / ذخیره — نمودار ترکیبی */
export function WaterBalanceChart({ data }: { data: BalancePoint[] }) {
  return (
    <div dir="ltr" className="w-full">
      <ResponsiveContainer width="100%" height={260}>
      <ComposedChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="t" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip />
        <Legend />
        <Bar dataKey="inflow" name="ورودی (mm)" fill="#0ea5e9" radius={[3, 3, 0, 0]} />
        <Bar dataKey="outflow" name="خروجی (mm)" fill="#f59e0b" radius={[3, 3, 0, 0]} />
        <Line type="monotone" dataKey="storage" name="ذخیره (mm)" stroke="#10b981" strokeWidth={2} dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
    </div>
  );
}
