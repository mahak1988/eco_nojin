import { HydraulicsCalculator, buildCalculatorLabels } from '../../components/dashboard/calculators';

export default {
  title: 'Dashboard/Calculators/Manning Channel',
  component: HydraulicsCalculator,
  parameters: {
    layout: 'padded',
  },
} as const;

export const English = () => (
  <div>
    <HydraulicsCalculator labels={buildCalculatorLabels('en').hydraulics} />
  </div>
);
English.storyName = 'English (LTR)';

export const Persian = () => (
  <div lang="fa" dir="rtl">
    <HydraulicsCalculator labels={buildCalculatorLabels('fa').hydraulics} />
  </div>
);
Persian.storyName = 'Persian (RTL)';