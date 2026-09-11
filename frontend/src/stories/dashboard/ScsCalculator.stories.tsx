import { ScsCalculator, buildCalculatorLabels } from '../../components/dashboard/calculators';

export default {
  title: 'Dashboard/Calculators/SCS-CN',
  component: ScsCalculator,
  parameters: {
    layout: 'padded',
  },
} as const;

export const English = () => (
  <div>
    <ScsCalculator labels={buildCalculatorLabels('en').scs} />
  </div>
);
English.storyName = 'English (LTR)';

export const Persian = () => (
  <div lang="fa" dir="rtl">
    <ScsCalculator labels={buildCalculatorLabels('fa').scs} />
  </div>
);
Persian.storyName = 'Persian (RTL)';