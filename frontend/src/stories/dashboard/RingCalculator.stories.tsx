import { RingCalculator, buildCalculatorLabels } from '../../components/dashboard/calculators';

export default {
  title: 'Dashboard/Calculators/Ring Storage',
  component: RingCalculator,
  parameters: {
    layout: 'padded',
  },
} as const;

export const English = () => (
  <div>
    <RingCalculator labels={buildCalculatorLabels('en').ring} />
  </div>
);
English.storyName = 'English (LTR)';

export const Persian = () => (
  <div lang="fa" dir="rtl">
    <RingCalculator labels={buildCalculatorLabels('fa').ring} />
  </div>
);
Persian.storyName = 'Persian (RTL)';