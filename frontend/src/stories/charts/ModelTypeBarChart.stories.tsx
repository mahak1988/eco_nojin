import { ModelTypeBarChart } from '../../components/dashboard/charts';

export default {
  title: 'Charts/ModelTypeBarChart',
  component: ModelTypeBarChart,
  parameters: {
    layout: 'centered',
  },
} as const;

export const English = () => <ModelTypeBarChart isFa={false} />;
English.storyName = 'English (LTR)';

export const Persian = () => <ModelTypeBarChart isFa={true} />;
Persian.storyName = 'Persian (RTL)';