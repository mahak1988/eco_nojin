import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group } from '../../../.storybook/states';
import { Select } from './Select';

const meta = {
  title: 'Forms/Select',
  component: Select,
  args: { label: sampleText.en.selectLabel },
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Select>;

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

/** Three options, the first selected. */
export const Default: Story = {
  render: (args) => (
    <div style={{ maxInlineSize: '18rem' }}>
      <Select {...args} defaultValue="30">
        <option value="10">{sampleText.en.selectOptionA}</option>
        <option value="30">{sampleText.en.selectOptionB}</option>
        <option value="60">{sampleText.en.selectOptionC}</option>
      </Select>
    </div>
  ),
};

/** The error state, resolved through the `--color-danger` token. */
export const ErrorState: Story = {
  name: 'Error — the danger token',
  args: { error: sampleText.en.selectError },
  render: (args) => (
    <div style={{ maxInlineSize: '18rem' }}>
      <Select {...args} defaultValue="">
        <option value="">{sampleText.en.selectOptionA}</option>
        <option value="30">{sampleText.en.selectOptionB}</option>
      </Select>
    </div>
  ),
};

/** Disabled, and disabled with an error, which should not read as editable. */
export const Disabled: Story = {
  render: () => (
    <div className="eco-grid">
      <Group label="disabled">
        <Select label={sampleText.en.selectLabel} defaultValue="30" disabled>
          <option value="30">{sampleText.en.selectOptionB}</option>
        </Select>
      </Group>
      <Group label="disabled with an error">
        <Select
          label={sampleText.en.selectLabel}
          defaultValue=""
          error={sampleText.en.selectError}
          disabled
        >
          <option value="">{sampleText.en.selectOptionA}</option>
        </Select>
      </Group>
    </div>
  ),
};

/** The five states, with a populated select as the content. */
export const States: Story = {
  name: 'The five states, through StateSlot',
  render: () => (
    <FiveStates title="Select in each of the five states">
      <div style={{ maxInlineSize: '18rem' }}>
        <Select label={sampleText.en.selectLabel} defaultValue="30">
          <option value="10">{sampleText.en.selectOptionA}</option>
          <option value="30">{sampleText.en.selectOptionB}</option>
          <option value="60">{sampleText.en.selectOptionC}</option>
        </Select>
      </div>
    </FiveStates>
  ),
};

/** Persian options, which is where a `<select>`'s own padding is most visible. */
export const InPersian: Story = {
  name: 'Persian options',
  parameters: { ecoLocale: 'fa' },
  render: () => (
    <div style={{ maxInlineSize: '18rem' }}>
      <Select label={sampleText.fa.selectLabel} defaultValue="30">
        <option value="10">{sampleText.fa.selectOptionA}</option>
        <option value="30">{sampleText.fa.selectOptionB}</option>
        <option value="60">{sampleText.fa.selectOptionC}</option>
      </Select>
    </div>
  ),
};
