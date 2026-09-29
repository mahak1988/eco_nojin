import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group, Stack } from '../../../.storybook/states';
import { Button } from './Button';

/**
 * ## About the strings in these stories
 *
 * Every literal in this directory is a *fixture*: sample data a page would have
 * resolved from the message catalogue and handed to the component as a prop. The
 * primitives carry no translatable copy on purpose — that is rule 1 of
 * `check-ui-kit.mjs`, and 53 public pages once broke it by carrying their own
 * `{ fa, en }` dictionaries. A story that inlined a label would assert the
 * opposite of the rule the stories exist to demonstrate, and the gate reads a
 * Persian literal in a JSX text position or a `label=` prop as exactly that
 * defect. So the fixtures live in `.storybook/labels.ts`, once, and follow the
 * toolbar's locale. Do not "fix" a story by moving its sample strings into
 * `messages/`; that is the page's job and the stories show the contract it owes.
 */

const meta = {
  title: 'Primitives/Button',
  component: Button,
  args: { children: 'Save' },
  argTypes: {
    variant: { control: 'select', options: ['primary', 'secondary', 'ghost', 'danger'] },
    size: { control: 'select', options: ['sm', 'md', 'lg'] },
    loading: { control: 'boolean' },
    disabled: { control: 'boolean' },
  },
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Button>;

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

/** The default a page gets: `variant="primary"`, `size="md"`. */
export const Default: Story = {};

/** The four variants `variantStyles` declares, in action order. */
export const Variants: RenderedStory = {
  name: 'Variants — primary, secondary, ghost, danger',
  render: () => (
    <Stack>
      <Group label="variant">
        <div className="eco-row">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Danger</Button>
        </div>
      </Group>
      <Group label="variant × disabled — a disabled button must still read as its variant">
        <div className="eco-row">
          <Button variant="primary" disabled>
            Primary
          </Button>
          <Button variant="secondary" disabled>
            Secondary
          </Button>
          <Button variant="ghost" disabled>
            Ghost
          </Button>
          <Button variant="danger" disabled>
            Danger
          </Button>
        </div>
      </Group>
    </Stack>
  ),
};

/** The three steps `sizeStyles` declares, against a real focus ring. */
export const Sizes: RenderedStory = {
  name: 'Sizes — sm, md, lg',
  render: () => (
    <Stack>
      <Group label="size">
        <div className="eco-row">
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
        </div>
      </Group>
      <Group label="label length at each step — the primary label is translated, so it grows">
        <div className="eco-row">
          <Button size="sm">{sampleText.fa.inputLabel}</Button>
          <Button size="md">{sampleText.fa.inputLabel}</Button>
          <Button size="lg">{sampleText.fa.inputLabel}</Button>
        </div>
      </Group>
    </Stack>
  ),
};

/**
 * `loading` sets `aria-busy` and `aria-disabled` and hides the label behind a
 * spinner, so the control keeps its width instead of collapsing while the
 * request is in flight.
 */
export const Loading: RenderedStory = {
  name: 'Loading — aria-busy, spinner, label held at full opacity of nothing',
  render: () => (
    <div className="eco-row">
      <Button loading>Saving</Button>
      <Button variant="secondary" loading>
        Fetching
      </Button>
      <Button variant="ghost" loading>
        Filtering
      </Button>
    </div>
  ),
};

/** The button as an icon-plus-label action, which is how the pages use it. */
export const WithIcon: RenderedStory = {
  name: 'With a leading glyph',
  render: () => (
    <div className="eco-row">
      <Button>
        <span aria-hidden="true">＋</span>
        New
      </Button>
      <Button variant="secondary">
        <span aria-hidden="true">↓</span>
        Export
      </Button>
    </div>
  ),
};

/**
 * A button has no data of its own, so its five states are the five states of the
 * thing it acts on. The useful review here is the one the composition shows: in
 * four of the five the action is genuinely not offered, and `StateSlot` carries
 * a retry affordance instead.
 */
export const States: RenderedStory = {
  name: 'The five states, through StateSlot',
  render: () => (
    <FiveStates title="Button in each of the five states">{<Button>Save</Button>}</FiveStates>
  ),
};
