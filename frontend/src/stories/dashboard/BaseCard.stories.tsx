import BaseCard from '../../components/dashboard/BaseCard';

export default {
  title: 'Dashboard/BaseCard',
  component: BaseCard,
  parameters: {
    layout: 'centered',
  },
} as const;

export const Leaf = () => (
  <BaseCard variant="leaf" title="Leaf Card">
    <p>Sample content for leaf card.</p>
  </BaseCard>
);
Leaf.storyName = 'Leaf Variant';

export const Sand = () => (
  <BaseCard variant="sand" title="Sand Card">
    <p>Sample content for sand card.</p>
  </BaseCard>
);
Sand.storyName = 'Sand Variant';

export const Aqua = () => (
  <BaseCard variant="aqua" title="Aqua Card">
    <p>Sample content for aqua card.</p>
  </BaseCard>
);
Aqua.storyName = 'Aqua Variant';

export const Night = () => (
  <BaseCard variant="night" title="Night Card">
    <p>Sample content for night card.</p>
  </BaseCard>
);
Night.storyName = 'Night Variant';

export const WithTooltip = () => (
  <BaseCard variant="leaf" title="Hover me" tooltip="This is a helpful tooltip">
    <p>Card with tooltip on hover.</p>
  </BaseCard>
);
WithTooltip.storyName = 'With Tooltip';

export const Draggable = () => (
  <BaseCard variant="aqua" title="Drag me" draggable>
    <p>Draggable card for dashboard customization.</p>
  </BaseCard>
);
Draggable.storyName = 'Draggable';