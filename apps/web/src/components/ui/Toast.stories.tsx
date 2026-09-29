import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group, Stack } from '../../../.storybook/states';
import { Button } from './Button';
import { Toast } from './Toast';

const meta = {
  title: 'Overlays/Toast',
  component: Toast,
  args: { title: sampleText.en.toastInfoTitle, duration: 0 },
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Toast>;

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
 * `duration={0}` disables the auto-dismiss timer, which is what every story here
 * does. A toast that closes after five seconds cannot be reviewed, and a
 * screenshot taken of a closed toast is a screenshot of nothing.
 */
export const Info: Story = {
  args: { variant: 'info', description: sampleText.en.paletteRunDescription, duration: 0 },
};

/** The four variants, each with its own inline-start border colour. */
export const Variants: RenderedStory = {
  name: 'Variants — info, success, warning, error',
  render: () => (
    <Stack>
      <Group label="info">
        <Toast variant="info" title={sampleText.en.toastInfoTitle} duration={0} />
      </Group>
      <Group label="success">
        <Toast variant="success" title={sampleText.en.toastSuccessTitle} duration={0} />
      </Group>
      <Group label="warning">
        <Toast variant="warning" title={sampleText.en.toastWarningTitle} duration={0} />
      </Group>
      <Group label="error">
        <Toast variant="error" title={sampleText.en.toastErrorTitle} duration={0} />
      </Group>
    </Stack>
  ),
};

/** With a description and an action, which is the shape a retry uses. */
export const WithDescriptionAndAction: Story = {
  name: 'With a description and an action',
  args: {
    variant: 'error',
    title: sampleText.en.toastErrorTitle,
    description: sampleText.en.inputError,
    duration: 0,
    action: <Button size="sm">{sampleText.en.toastAction}</Button>,
  },
};

/**
 * The close affordance. Its `aria-label` is the literal string `Dismiss` inside
 * the component, so it is announced in English in all fourteen locales — reported
 * rather than worked around, because the prop does not exist.
 */
export const CloseAffordance: RenderedStory = {
  name: 'The close button — its aria-label is a hard-coded English string',
  render: () => (
    <div style={{ display: 'grid', placeItems: 'center', minBlockSize: '12rem' }}>
      <Toast title={sampleText.en.toastInfoTitle} duration={0} />
    </div>
  ),
};

/** The five states, with the toast as the content of the ready state. */
export const States: RenderedStory = {
  name: 'The five states, through StateSlot',
  render: () => (
    <FiveStates title="Toast in each of the five states">
      <Toast
        variant="success"
        title={sampleText.en.toastSuccessTitle}
        description={sampleText.en.dialogDescription}
        duration={0}
      />
    </FiveStates>
  ),
};

/** Persian title and description, with the toast's own RTL alignment. */
export const InPersian: Story = {
  name: 'Persian title and description',
  parameters: { ecoLocale: 'fa' },
  args: {
    variant: 'warning',
    title: sampleText.fa.toastWarningTitle,
    description: sampleText.fa.offlineMessage,
    duration: 0,
  },
};
