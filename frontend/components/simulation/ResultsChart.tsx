import { Card, CardContent } from '../ui/card'; // Updated import path
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

type SimulationResult = {
  year: number;
  yield: number;
  profit: number;
  co2_absorbed: number;
  water_usage: number;
};

interface ResultsChartProps {
  data: SimulationResult[];
}

export function ResultsChart({ data }: ResultsChartProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={data}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
            <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
            <Tooltip />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="yield" stroke="#8884d8" name="Yield (tons)" activeDot={{ r: 8 }} />
            <Line yAxisId="left" type="monotone" dataKey="profit" stroke="#ffc658" name="Profit ($)" />
            <Line yAxisId="right" type="monotone" dataKey="co2_absorbed" stroke="#82ca9d" name="CO2 Absorbed (tons)" />
            <Line yAxisId="right" type="monotone" dataKey="water_usage" stroke="#ff7300" name="Water Usage (L)" />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}