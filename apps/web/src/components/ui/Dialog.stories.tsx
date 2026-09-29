import type { Meta, StoryObj } from '@storybook/react-vite';
import { useState } from 'react';
import { sampleText } from '../../../.storybook/fixtures';
import { Group, Stack } from '../../../.storybook/states';
import { Button } from './Button';
import { Dialog } from './Dialog';

const meta = {
  title: 'Overlays/Dialog',
  component: Dialog,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Dialog>;

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
 * Open on load, so the frame a reviewer photographs is the open dialog and not the
 * trigger. The component portals to `document.body`, so it is positioned against
 * the preview viewport exactly as it is against the real one.
 *
 * A native `<dialog>` with `open` set does not become modal, so the browser does
 * not trap focus for it — the component traps `Tab` itself and closes on
 * `Escape`, and the header it renders is a real `<h2>` labelled by `title`.
 */
export const Default: Story = {
  name: 'Open, with a description',
  render: function OpenDialog() {
    const [open, setOpen] = useState(true);
    return (
      <>
        <Button variant="secondary" onClick={() => setOpen(true)}>
          {sampleText.en.dialogConfirm}
        </Button>
        <Dialog
          open={open}
          onOpenChange={setOpen}
          title={sampleText.en.dialogTitle}
          description={sampleText.en.dialogDescription}
        >
          <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>{sampleText.en.dialogBody}</p>
        </Dialog>
      </>
    );
  },
};

/** Without a description, which is the case where `aria-describedby` is dropped. */
export const WithoutDescription: Story = {
  render: function MinimalDialog() {
    const [open, setOpen] = useState(true);
    return (
      <Dialog open={open} onOpenChange={setOpen} title={sampleText.en.dialogTitle}>
        <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>{sampleText.en.dialogBody}</p>
      </Dialog>
    );
  },
};

/** A dialog with more than one focusable element, so the focus trap is visible. */
export const WithFocusableContent: Story = {
  name: 'With focusable content — Tab cycles inside',
  render: function FocusableDialog() {
    const [open, setOpen] = useState(true);
    return (
      <Dialog
        open={open}
        onOpenChange={setOpen}
        title={sampleText.en.dialogTitle}
        description={sampleText.en.dialogDescription}
      >
        <Stack>
          <Group label="the first focusable element receives focus on open">
            <Button variant="secondary">Keep readings</Button>
          </Group>
          <Group label="the last one, which is where the trap wraps from">
            <Button variant="danger">{sampleText.en.dialogConfirm}</Button>
          </Group>
        </Stack>
      </Dialog>
    );
  },
};

/** Persian title and description, with the cancel affordance in Persian. */
export const InPersian: Story = {
  name: 'Persian title and description',
  parameters: { ecoLocale: 'fa' },
  render: function PersianDialog() {
    const [open, setOpen] = useState(true);
    return (
      <Dialog
        open={open}
        onOpenChange={setOpen}
        title={sampleText.fa.dialogTitle}
        description={sampleText.fa.dialogDescription}
      >
        <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>{sampleText.fa.dialogBody}</p>
      </Dialog>
    );
  },
};
