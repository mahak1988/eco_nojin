import { VgCalculator, buildCalculatorLabels } from '../../components/dashboard/calculators';

export default {
  title: 'Dashboard/Calculators/Van Genuchten',
  component: VgCalculator,
  parameters: {
    layout: 'padded',
  },
} as const;

export const English = () => (
  <div>
    <VgCalculator labels={buildCalculatorLabels('en').vg} />
  </div>
);
English.storyName = 'English (LTR)';

export const Persian = () => (
  <div lang="fa" dir="rtl">
    <VgCalculator labels={buildCalculatorLabels('fa').vg} />
  </div>
);
Persian.storyName = 'Persian (RTL)';