import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group } from '../../../.storybook/states';
import { Input } from './Input';

const meta = {
  title: 'Forms/Input',
  component: Input,
  args: { label: sampleText.en.inputLabel, placeholder: sampleText.en.inputPlaceholder },
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Input>;

export default meta;

/**
 * A story that supplies its own `render`, and therefore its own arguments.
 *
 * `StoryObj<typeof meta>` makes every prop the component declares a *required*
 * `args` key whenever the meta has no `args` block of its own, which is exactly
 * what happens in a file whose stories all build their arguments inside
 * `render`. The requirement has no runtime meaning there — the controls panel is
 * not wired, by design — so the bare `StoryObj` is used instead. The component
 * itself is type-checked regardless; this file simply has no story that reads
 * `args`, so the strict alias would have no user.
 */
type Story = StoryObj;

/** A labelled field with a placeholder and a hint. */
export const Default: Story = {
  args: { id: 'site-name', 'aria-describedby': 'site-name-hint' },
  render: (args) => (
    <div style={{ maxInlineSize: '22rem' }}>
      <Input {...args} />
      <p
        id="site-name-hint"
        style={{ margin: 'var(--space-2) 0 0', color: 'var(--color-ink-soft)' }}
      >
        {sampleText.en.inputHint}
      </p>
    </div>
  ),
};

/**
 * The error state.
 *
 * `border-danger` and `text-danger` are the two classes that resolve through the
 * `--color-danger` token, which is itself an alias of `--clay`. A field in an
 * error state that looks exactly like a normal one is the defect that alias
 * exists to prevent, so it is worth a story of its own.
 */
export const ErrorState: Story = {
  name: 'Error — the danger token',
  args: { error: sampleText.en.inputError, defaultValue: '' },
  render: (args) => (
    <div style={{ maxInlineSize: '22rem' }}>
      <Input {...args} />
    </div>
  ),
};

/** Disabled and read-only, which are different and both used by the forms. */
export const DisabledAndReadOnly: Story = {
  name: 'Disabled and read-only',
  render: () => (
    <div className="eco-grid">
      <Group label="disabled">
        <Input label={sampleText.en.inputLabel} defaultValue="Urmia lake north" disabled />
      </Group>
      <Group label="read-only">
        <Input label={sampleText.en.inputLabel} defaultValue="site-0014" readOnly />
      </Group>
    </div>
  ),
};

/** Every input `type` the forms reach for, so the field box is not a one-off. */
export const Types: Story = {
  name: 'Types',
  render: () => (
    <div className="eco-grid">
      <Group label="text">
        <Input type="text" label={sampleText.en.inputLabel} />
      </Group>
      <Group label="email">
        <Input type="email" label="Email" />
      </Group>
      <Group label="number">
        <Input type="number" label="Sampling depth" defaultValue={30} />
      </Group>
      <Group label="date">
        <Input type="date" label="Sample date" />
      </Group>
      <Group label="search">
        <Input type="search" label="Find a site" />
      </Group>
      <Group label="file">
        <Input type="file" label="Field photo" />
      </Group>
    </div>
  ),
};

/** The five states, with a filled field as the content. */
export const States: Story = {
  name: 'The five states, through StateSlot',
  render: () => (
    <FiveStates title="Input in each of the five states">
      <div style={{ maxInlineSize: '22rem' }}>
        <Input label={sampleText.en.inputLabel} defaultValue="Urmia lake north" />
      </div>
    </FiveStates>
  ),
};

/**
 * Persian label and error together. The label is `block text-sm … text-ink` with
 * a `mb-1.5`; under `dir="rtl"` the physical margin is still vertical so this one
 * is safe, but the field's `px-3` inset has to mirror, and this is the frame
 * that shows it.
 */
export const InPersian: Story = {
  name: 'Persian label and error',
  parameters: { ecoLocale: 'fa' },
  render: () => (
    <div style={{ maxInlineSize: '22rem' }}>
      <Input
        label={sampleText.fa.inputLabel}
        placeholder={sampleText.fa.inputPlaceholder}
        error={sampleText.fa.inputError}
      />
    </div>
  ),
};
