import { CategoryPieChart } from '../../components/dashboard/charts';

export default {
  title: 'Charts/CategoryPieChart',
  component: CategoryPieChart,
  parameters: {
    layout: 'centered',
  },
} as const;

export const English = () => <CategoryPieChart isFa={false} />;
English.storyName = 'English (LTR)';

export const Persian = () => <CategoryPieChart isFa={true} />;
Persian.storyName = 'Persian (RTL)';