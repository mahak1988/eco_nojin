import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group } from '../../../.storybook/states';
import { Switch } from './Switch';

const meta = {
  title: 'Forms/Switch',
  component: Switch,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Switch>;

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

/**
 * A `role="switch"` button carries no label of its own, so every story here
 * labels it from outside.
 *
 * The labelling pattern is the finding, not an accident. `Switch` renders a
 * `<button>`, and a `<button>` is not a *labelable* element, so the obvious
 * `<label>…<Switch/>…</label>` associates nothing: clicking the text does not
 * toggle the switch, and the accessible name stays whatever `aria-label` said.
 * `noLabelWithoutControl` in the Biome run is what surfaced it. Every consumer
 * therefore has to hand-wire an id and an `aria-labelledby`, which is why the
 * helpers below exist — a component that cannot be labelled the way every other
 * form control in the kit can is a defect in the component, not in the caller.
 *
 * Switch the toolbar to `fa` before signing this off: the knob is moved with
 * `translate-x-6` / `translate-x-1`, which are physical transforms, so the
 * travel does not mirror.
 */
export const Default: Story = {
  name: 'On and off',
  render: () => (
    <div className="eco-grid">
      <Group label="off">
        <LabelledSwitch id="switch-off" checked={false} />
      </Group>
      <Group label="on">
        <LabelledSwitch id="switch-on" checked />
      </Group>
    </div>
  ),
};

/** With the description a settings row carries underneath the label. */
export const WithDescription: Story = {
  render: function SettingsRow() {
    return (
      <div
        style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: 'var(--space-3)',
          maxInlineSize: '28rem',
        }}
      >
        <Switch aria-labelledby="switch-label" aria-describedby="switch-desc" checked />
        <span style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
          <span id="switch-label" style={{ fontWeight: 600 }}>
            {sampleText.en.switchLabel}
          </span>
          <span id="switch-desc" style={{ color: 'var(--color-ink-soft)', fontSize: '0.875rem' }}>
            {sampleText.en.switchDescription}
          </span>
        </span>
      </div>
    );
  },
};

/** Disabled on and off, which is what a permission the reader lacks looks like. */
export const Disabled: Story = {
  render: () => (
    <div className="eco-row">
      <Switch aria-label={sampleText.en.switchLabel} checked disabled />
      <Switch aria-label={sampleText.en.switchLabel} checked={false} disabled />
    </div>
  ),
};

/** The five states, with the switch as persistent page chrome. */
export const States: Story = {
  name: 'The five states, through StateSlot',
  render: () => (
    <FiveStates title="Switch in each of the five states">
      <LabelledSwitch id="switch-states" checked />
    </FiveStates>
  ),
};

/** Persian label, at the same size. */
export const InPersian: Story = {
  name: 'Persian label',
  parameters: { ecoLocale: 'fa' },
  render: () => <LabelledSwitch id="switch-fa" label={sampleText.fa.switchLabel} checked />,
};

/** The pattern a page has to use, because `<label>` does not work here. */
function LabelledSwitch({
  id,
  label = sampleText.en.switchLabel,
  checked,
}: {
  id: string;
  label?: string;
  checked: boolean;
}) {
  return (
    <span style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
      <Switch aria-labelledby={id} checked={checked} />
      <span id={id}>{label}</span>
    </span>
  );
}
