import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group, Stack } from '../../../.storybook/states';
import { Progress } from './Progress';

const meta = {
  title: 'Data/Progress',
  component: Progress,
  args: { label: sampleText.en.progressLabel, value: 63, detail: sampleText.en.progressDetail },
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Progress>;

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

/** Determinate, with the visible label and the `detail` on the inline end. */
export const Default: Story = {};

/**
 * Indeterminate omits `aria-valuenow` entirely rather than sending 0. That is
 * the difference between "the value is unknown" and "zero per cent complete",
 * which are different claims, and only a story that renders both can be checked
 * for it.
 */
export const Indeterminate: RenderedStory = {
  name: 'Indeterminate — no aria-valuenow',
  render: () => (
    <Stack>
      <Group label="indeterminate">
        <Progress label={sampleText.en.progressLabel} />
      </Group>
      <Group label="indeterminate, label hidden — the bar then has to carry its own name">
        <Progress label={sampleText.en.progressLabel} hideLabel />
      </Group>
    </Stack>
  ),
};

/** The four tones. */
export const Tones: RenderedStory = {
  name: 'Tones — info, success, warn, bad',
  render: () => (
    <Stack>
      {(['info', 'success', 'warn', 'bad'] as const).map((tone) => (
        <Group key={tone} label={tone}>
          <Progress label={sampleText.en.progressLabel} value={48} tone={tone} />
        </Group>
      ))}
    </Stack>
  ),
};

/**
 * The three track heights, named `size` here rather than `density`. These are
 * the same three steps the rest of the kit calls cozy / compact / dense, which is
 * worth a reviewer's attention: one vocabulary, two names.
 */
export const Sizes: RenderedStory = {
  name: 'Sizes — cozy, compact, dense',
  render: () => (
    <Stack>
      {(['cozy', 'compact', 'dense'] as const).map((size) => (
        <Group key={size} label={size}>
          <Progress label={sampleText.en.progressLabel} value={72} size={size} />
        </Group>
      ))}
    </Stack>
  ),
};

/** A partial result, which is the state the master plan wants declared out loud. */
export const PartialValue: RenderedStory = {
  name: 'A partial result, labelled as one',
  render: () => (
    <Progress
      label={sampleText.en.progressLabel}
      value={7}
      detail={sampleText.en.progressDetail}
      tone="warn"
    />
  ),
};

/**
 * The five states. A progress bar in the empty state is a bar at zero with a
 * different tone, not a different component — that is the point of showing all
 * six rows together.
 */
export const States: RenderedStory = {
  name: 'The five states, through StateSlot',
  render: () => (
    <FiveStates title="Progress in each of the five states">
      <Progress
        label={sampleText.en.progressLabel}
        value={63}
        detail={sampleText.en.progressDetail}
      />
    </FiveStates>
  ),
};
