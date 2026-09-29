import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group, Stack } from '../../../.storybook/states';
import { Skeleton } from './Skeleton';

const meta = {
  title: 'Data/Skeleton',
  component: Skeleton,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Skeleton>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * A story that supplies its own `render`, and therefore its own arguments.
 *
 * `StoryObj<typeof meta>` makes every prop the component declares a *required*
 * `args` key whenever the meta has no `args` block of its own, which is exactly
 * what happens in a file whose stories build their arguments inside `render`. The
 * requirement has no runtime meaning there — the controls panel is not wired, by
 * design — so those stories are typed with the bare `StoryObj` instead. Stories
 * that do read `args` keep the strict alias, and the components themselves are
 * type-checked regardless.
 */
type RenderedStory = StoryObj;

/** One line of text placeholder. */
export const Default: Story = {};

/**
 * Every variant. A skeleton is a claim about the shape of what is coming, so the
 * variants are worth photographing together: a `card` placeholder that does not
 * match the real card is a layout shift the reader pays for.
 */
export const Variants: RenderedStory = {
  name: 'Variants — text, card, stat, table-row, circular, rectangular',
  render: () => (
    <Stack>
      <Group label="text, three lines with a short last line">
        <Skeleton variant="text" lines={3} />
      </Group>
      <Group label="card">
        <Skeleton variant="card" />
      </Group>
      <Group label="stat">
        <Skeleton variant="stat" />
      </Group>
      <Group label="table-row ×3">
        <div>
          <Skeleton variant="table-row" />
          <Skeleton variant="table-row" />
          <Skeleton variant="table-row" />
        </div>
      </Group>
      <Group label="circular and rectangular">
        <div className="eco-row">
          <Skeleton variant="circular" width={40} height={40} />
          <Skeleton variant="rectangular" width={180} height={40} />
        </div>
      </Group>
    </Stack>
  ),
};

/** The table shape a reader will actually meet. */
export const AsATableLoadingState: RenderedStory = {
  name: 'As a table in the loading state',
  render: () => (
    <Stack>
      <Group label="caption">
        <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>{sampleText.en.tableCaption}</p>
      </Group>
      <div>
        <Skeleton variant="table-row" />
        <Skeleton variant="table-row" />
        <Skeleton variant="table-row" />
        <Skeleton variant="table-row" />
      </div>
    </Stack>
  ),
};

/**
 * The five states, with skeletons as the loading content.
 *
 * This is the composition the plan asks for: a page that is loading shows a
 * skeleton, not the empty message, so the reader is told the answer is coming
 * rather than that there is nothing there.
 */
export const States: RenderedStory = {
  name: 'The five states, through StateSlot',
  render: () => (
    <FiveStates title="Skeleton in each of the five states">
      <Stack label={sampleText.en.skeletonCaption}>
        <Skeleton variant="stat" />
        <Skeleton variant="text" lines={3} />
      </Stack>
    </FiveStates>
  ),
};
