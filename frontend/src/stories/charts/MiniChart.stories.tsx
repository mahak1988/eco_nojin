import MiniChart from '../../components/dashboard/MiniChart';

export default {
  title: 'Charts/MiniChart',
  component: MiniChart,
  parameters: {
    layout: 'centered',
  },
} as const;

const demoData = [
  { x: 0, y: 130 },
  { x: 1, y: 95 },
  { x: 2, y: 72 },
  { x: 3, y: 55 },
  { x: 4, y: 45 },
  { x: 5, y: 40 },
  { x: 6, y: 38 },
];

export const InfiltrationRate = () => (
  <MiniChart 
    series={demoData}
    yLabel="f(t) mm/h"
    xLabel="t (h)"
  />
);
InfiltrationRate.storyName = 'Horton Infiltration Rate';

export const Cumulative = () => (
  <MiniChart 
    series={[
      { x: 0, y: 0 },
      { x: 1, y: 110 },
      { x: 2, y: 190 },
      { x: 3, y: 250 },
      { x: 4, y: 290 },
      { x: 5, y: 315 },
      { x: 6, y: 330 },
    ]}
    yLabel="F(t) mm"
    xLabel="t (h)"
  />
);
Cumulative.storyName = 'Cumulative Infiltration';

export const RunoffCurve = () => (
  <MiniChart 
    series={[
      { x: 0, y: 0 },
      { x: 10, y: 1 },
      { x: 20, y: 5 },
      { x: 30, y: 12 },
      { x: 40, y: 25 },
      { x: 50, y: 45 },
      { x: 60, y: 68 },
      { x: 80, y: 118 },
      { x: 100, y: 174 },
    ]}
    yLabel="Q mm"
    xLabel="P mm"
  />
);
RunoffCurve.storyName = 'SCS-CN Runoff Curve';