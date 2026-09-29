import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { stateLabels } from '../../../.storybook/labels';
import { FiveStates, Group, Stack } from '../../../.storybook/states';
import { Card } from './Card';
import { StateSlot } from './StateSlot';

const meta = {
  title: 'Data/StateSlot',
  component: StateSlot,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof StateSlot>;

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

/**
 * Every label is a required prop, which is what makes the component
 * translatable. This object is the whole contract a page has to satisfy; the
 * strings in it come from the story fixture set, not from the component.
 *
 * Declared before the stories that use it so that reading the file top to bottom
 * meets the vocabulary before the examples.
 */
const LABELS = stateLabels('fa');

/**
 * `ready` renders the children and nothing else — no wrapper, no card, no live
 * region. A component that adds a box to the happy path is a component that
 * changes the layout of every page that uses it.
 */
export const Ready: Story = {
  name: 'Ready — children only, no wrapper',
  args: {
    state: 'ready',
    labels: stateLabels(),
    children: (
      <Card density="compact">
        <p style={{ margin: 0, color: 'var(--color-ink)' }}>{sampleText.en.cardBody}</p>
      </Card>
    ),
  },
};

/**
 * The component that defines the vocabulary, shown one state at a time so the
 * tone mapping is legible: `error` is the only bad one, `partial` and `offline`
 * are warn, and `loading` and `empty` are neutral.
 */
export const OneAtATime: RenderedStory = {
  name: 'One state at a time — the tone mapping',
  render: () => (
    <Stack>
      <Group label="loading · neutral">
        <StateSlot state="loading" labels={LABELS}>
          <p>—</p>
        </StateSlot>
      </Group>
      <Group label="empty · neutral">
        <StateSlot state="empty" labels={LABELS}>
          <p>—</p>
        </StateSlot>
      </Group>
      <Group label="error · bad, role=alert">
        <StateSlot state="error" labels={LABELS} onRetry={() => {}}>
          <p>—</p>
        </StateSlot>
      </Group>
      <Group label="partial · warn, with the detail that declares the limit">
        <StateSlot state="partial" labels={LABELS} detail={sampleText.en.progressDetail}>
          <p>—</p>
        </StateSlot>
      </Group>
      <Group label="offline · warn, with a retry">
        <StateSlot state="offline" labels={LABELS} onRetry={() => {}}>
          <p>—</p>
        </StateSlot>
      </Group>
    </Stack>
  ),
};

/**
 * The retry affordance. This is the one control `StateSlot` renders by hand
 * rather than composing from `Button`, so it is the frame where the two are
 * compared — and the reviewer should notice the difference.
 */
export const WithRetry: Story = {
  name: 'With a retry affordance',
  args: { state: 'error', labels: LABELS, onRetry: () => {}, children: <p>—</p> },
};

/** Without one, on purpose: a passive state has no action to offer. */
export const WithoutRetry: Story = {
  name: 'Without a retry affordance',
  args: { state: 'error', labels: LABELS, children: <p>—</p> },
};

/** The density it forwards to `Card`. */
export const Densities: RenderedStory = {
  name: 'Densities — cozy, compact, dense',
  render: () => (
    <Stack>
      {(['cozy', 'compact', 'dense'] as const).map((density) => (
        <Group key={density} label={density}>
          <StateSlot state="empty" labels={LABELS} density={density}>
            <p>—</p>
          </StateSlot>
        </Group>
      ))}
    </Stack>
  ),
};

/** All six, in the order the master plan lists them. */
export const States: RenderedStory = {
  name: 'All five states plus ready',
  render: () => (
    <FiveStates title="StateSlot in each state" action>
      <Card density="compact">
        <p style={{ margin: 0 }}>{sampleText.en.cardBody}</p>
      </Card>
    </FiveStates>
  ),
};
