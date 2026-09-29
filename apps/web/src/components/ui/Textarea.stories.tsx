import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group } from '../../../.storybook/states';
import { Textarea } from './Textarea';

const meta = {
  title: 'Forms/Textarea',
  component: Textarea,
  args: { label: sampleText.en.textareaLabel, placeholder: sampleText.en.textareaPlaceholder },
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Textarea>;

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

/** A labelled multi-line field, empty. */
export const Default: Story = {
  render: (args) => (
    <div style={{ maxInlineSize: '28rem' }}>
      <Textarea {...args} />
    </div>
  ),
};

/** The error state, resolved through the `--color-danger` token. */
export const ErrorState: Story = {
  name: 'Error — the danger token',
  args: { error: sampleText.en.textareaError },
  render: (args) => (
    <div style={{ maxInlineSize: '28rem' }}>
      <Textarea {...args} />
    </div>
  ),
};

/** With content, disabled, and resized by the reader. */
export const FilledDisabledAndResized: Story = {
  name: 'Filled, disabled, and reader-resized',
  render: () => (
    <div className="eco-grid">
      <Group label="filled">
        <Textarea
          label={sampleText.en.textareaLabel}
          defaultValue="Canopy recovered on the north slope after the third visit. Two points still offline."
        />
      </Group>
      <Group label="disabled">
        <Textarea
          label={sampleText.en.textareaLabel}
          defaultValue="Read-only field note"
          disabled
        />
      </Group>
      <Group label="resize: vertical">
        <Textarea
          label={sampleText.en.textareaLabel}
          style={{ resize: 'vertical', minBlockSize: '5rem' }}
        />
      </Group>
    </div>
  ),
};

/** The five states, with a filled field as the content. */
export const States: Story = {
  name: 'The five states, through StateSlot',
  render: () => (
    <FiveStates title="Textarea in each of the five states">
      <div style={{ maxInlineSize: '28rem' }}>
        <Textarea
          label={sampleText.en.textareaLabel}
          defaultValue="Canopy recovered on the north slope."
        />
      </div>
    </FiveStates>
  ),
};

/** Persian label, placeholder and error together. */
export const InPersian: Story = {
  name: 'Persian label, placeholder and error',
  parameters: { ecoLocale: 'fa' },
  render: () => (
    <div style={{ maxInlineSize: '28rem' }}>
      <Textarea
        label={sampleText.fa.textareaLabel}
        placeholder={sampleText.fa.textareaPlaceholder}
        error={sampleText.fa.textareaError}
      />
    </div>
  ),
};
