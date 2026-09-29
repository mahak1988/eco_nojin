import type { Meta, StoryObj } from '@storybook/react-vite';
import { useState } from 'react';
import { sampleText } from '../../../.storybook/fixtures';
import { Group, Stack } from '../../../.storybook/states';
import { CommandPalette, type CommandPaletteItem } from './CommandPalette';

const meta = {
  title: 'Overlays/CommandPalette',
  component: CommandPalette,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof CommandPalette>;

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

function makeItems(onRun: (label: string) => void): CommandPaletteItem[] {
  return [
    {
      id: 'run',
      label: sampleText.en.paletteItemRun,
      description: sampleText.en.paletteRunDescription,
      shortcut: '⌘R',
      icon: <span aria-hidden="true">▤</span>,
      action: () => onRun(sampleText.en.paletteItemRun),
    },
    {
      id: 'describe',
      label: sampleText.en.paletteItemDescribe,
      description: sampleText.en.paletteDescribeDescription,
      shortcut: '⌘D',
      action: () => onRun(sampleText.en.paletteItemDescribe),
    },
    {
      id: 'export',
      label: sampleText.en.paletteItemExport,
      description: sampleText.en.paletteExportDescription,
      shortcut: '⌘E',
      action: () => onRun(sampleText.en.paletteItemExport),
    },
  ];
}

/**
 * Open, with three commands. The palette traps `ArrowUp` / `ArrowDown` on the
 * input and moves `aria-activedescendant` with the selection, so the list is
 * announced rather than focused.
 *
 * Read the chrome: `Search commands`, `Command palette` and `No commands found`
 * are literals inside the component, and so is the `Search commands...` default
 * placeholder. Every other component in the kit takes those as props. This is the
 * frame where that difference is visible, and it is reported rather than worked
 * around — the stories pass `placeholder` in, and the rest cannot be passed in
 * at all.
 */
export const Default: Story = {
  name: 'Open, with three commands',
  render: function OpenPalette() {
    const [open, setOpen] = useState(true);
    const [ran, setRan] = useState('');
    return (
      <>
        <Stack>
          <Group label="the trigger, for context">
            <button
              type="button"
              onClick={() => setOpen(true)}
              style={{
                padding: 'var(--space-2) var(--space-4)',
                borderRadius: 'var(--radius-8)',
                border: '1px solid var(--color-line)',
                background: 'var(--color-surface)',
                color: 'var(--color-ink)',
                cursor: 'pointer',
              }}
            >
              {sampleText.en.paletteSearch}
            </button>
          </Group>
          {ran ? (
            <p style={{ margin: 0, color: 'var(--color-ink-soft)' }} role="status">
              {ran}
            </p>
          ) : null}
        </Stack>
        <CommandPalette
          open={open}
          onOpenChange={setOpen}
          items={makeItems(setRan)}
          placeholder={sampleText.en.paletteSearch}
        />
      </>
    );
  },
};

/** A query that matches nothing, which is the empty state of a listbox. */
export const NoMatches: Story = {
  name: 'No matches — the empty state is a hard-coded English string',
  render: function NoMatches() {
    const [open, setOpen] = useState(true);
    return (
      <CommandPalette
        open={open}
        onOpenChange={setOpen}
        items={makeItems(() => {})}
        placeholder="zzzz"
      />
    );
  },
};

/** An empty command set, so the reader never sees a list at all. */
export const NoCommands: Story = {
  name: 'No commands registered',
  render: function NoCommands() {
    const [open, setOpen] = useState(true);
    return <CommandPalette open={open} onOpenChange={setOpen} items={[]} />;
  },
};

/**
 * Persian commands, matching on a Persian query. The palette centres itself with
 * `inset-inline: 0` plus auto margins, so the frame is the check that a logical
 * centring survives a mirrored document.
 */
export const InPersian: Story = {
  name: 'Persian commands',
  parameters: { ecoLocale: 'fa' },
  render: function PersianPalette() {
    const [open, setOpen] = useState(true);
    return (
      <CommandPalette
        open={open}
        onOpenChange={setOpen}
        placeholder={sampleText.fa.paletteSearch}
        items={[
          {
            id: 'run',
            label: sampleText.fa.paletteItemRun,
            description: sampleText.fa.paletteRunDescription,
            action: () => {},
          },
          {
            id: 'describe',
            label: sampleText.fa.paletteItemDescribe,
            description: sampleText.fa.paletteDescribeDescription,
            action: () => {},
          },
        ]}
      />
    );
  },
};
