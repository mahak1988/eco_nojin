import { HortonCalculator, buildCalculatorLabels } from '../../components/dashboard/calculators';

export default {
  title: 'Dashboard/Calculators/Horton',
  component: HortonCalculator,
  parameters: {
    layout: 'padded',
  },
} as const;

export const English = () => (
  <div>
    <HortonCalculator labels={buildCalculatorLabels('en').horton} />
  </div>
);
English.storyName = 'English (LTR)';

export const Persian = () => (
  <div lang="fa" dir="rtl">
    <HortonCalculator labels={buildCalculatorLabels('fa').horton} />
  </div>
);
Persian.storyName = 'Persian (RTL)';