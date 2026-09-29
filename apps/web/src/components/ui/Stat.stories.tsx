import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group, Stack } from '../../../.storybook/states';
import { Skeleton } from './Skeleton';
import { Stat } from './Stat';

const meta = {
  title: 'Data/Stat',
  component: Stat,
  args: { label: sampleText.en.statLabel, value: '68.4', unit: '%' },
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Stat>;

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

/** A single number, isolated, tabular figures, no trend. */
export const Default: Story = {};

/**
 * The three sizes. `Stat` sets `direction: ltr` and `unicode-bidi: isolate` on
 * itself, which is the reason a Latin numeral inside a Persian paragraph keeps
 * its own order — this is the frame that shows whether the value and its unit
 * still read correctly at each step.
 */
export const Sizes: RenderedStory = {
  name: 'Sizes — sm, md, lg',
  render: () => (
    <Stack>
      {(['sm', 'md', 'lg'] as const).map((size) => (
        <Group key={size} label={size}>
          <Stat label={sampleText.en.statLabel} value="68.4" unit="%" size={size} />
        </Group>
      ))}
    </Stack>
  ),
};

/** The three trend directions, and a trend with no arrow. */
export const Trends: RenderedStory = {
  name: 'Trends — up, down, neutral',
  render: () => (
    <Stack>
      <Group label="trend">
        <div className="eco-row" style={{ alignItems: 'flex-start' }}>
          <Stat
            label={sampleText.en.statLabel}
            value="68.4"
            unit="%"
            trend="up"
            trendValue={sampleText.en.statTrendUp}
          />
          <Stat
            label={sampleText.en.statLabel}
            value="51.2"
            unit="%"
            trend="down"
            trendValue={sampleText.en.statTrendDown}
          />
          <Stat
            label={sampleText.en.statLabel}
            value="51.2"
            unit="%"
            trend="neutral"
            trendValue={sampleText.en.statTrendUp}
          />
        </div>
      </Group>
    </Stack>
  ),
};

/**
 * With a provenance stamp.
 *
 * This is the frame where the library's copy rule is visible: the stamp falls
 * back to the literal string `Unknown source` when no `source` is given, and
 * `Verified` is announced as a hard-coded `aria-label`. Both are English inside a
 * component that is otherwise prop-driven — see the defect report.
 */
export const WithProvenance: Story = {
  name: 'With a provenance stamp',
  args: {
    provenance: {
      source: sampleText.en.statProvenanceSource,
      verified: true,
      method: sampleText.en.statProvenanceMethod,
      timestamp: '2026-08-12T00:00:00Z',
    },
  },
};

/** The same stamp with no `source`, which is where the hard-coded fallback shows. */
export const ProvenanceWithoutSource: Story = {
  name: 'Provenance with no source — the component invents a fallback string',
  args: { provenance: { verified: false, timestamp: '2026-08-12T00:00:00Z' } },
};

/** The five states, with the loading state holding a skeleton of the same shape. */
export const States: RenderedStory = {
  name: 'The five states, through StateSlot',
  render: () => (
    <FiveStates title="Stat in each of the five states">
      <Stat
        label={sampleText.en.statLabel}
        value="68.4"
        unit="%"
        trend="up"
        trendValue={sampleText.en.statTrendUp}
        provenance={{ source: sampleText.en.statProvenanceSource, verified: true }}
      />
    </FiveStates>
  ),
};

/** The loading composition: a `Skeleton` in the `stat` variant, same footprint. */
export const LoadingSkeleton: RenderedStory = {
  name: 'Loading — the same footprint, filled by a stat skeleton',
  render: () => <Skeleton variant="stat" />,
};
