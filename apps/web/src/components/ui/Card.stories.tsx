import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { Group, Stack } from '../../../.storybook/states';
import { Card } from './Card';

const meta = {
  title: 'Primitives/Card',
  component: Card,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Card>;

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

/** `density="cozy"` with a heading and a paragraph. */
export const Default: Story = {
  args: {
    children: (
      <>
        <h3 style={{ margin: 0, fontSize: '1.125rem' }}>{sampleText.en.cardTitle}</h3>
        <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>{sampleText.en.cardBody}</p>
      </>
    ),
  },
};

/**
 * The three steps against the same content, so the difference is padding and gap
 * and nothing else. `Card` is the density primitive the rest of the kit forwards
 * to, which is why the gate demands the three literals here.
 */
export const Densities: RenderedStory = {
  name: 'Densities — cozy, compact, dense',
  render: () => (
    <Stack>
      {(['cozy', 'compact', 'dense'] as const).map((density) => (
        <Group key={density} label={density}>
          <Card density={density}>
            <h3 style={{ margin: 0, fontSize: '1.125rem' }}>{sampleText.en.cardTitle}</h3>
            <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>{sampleText.en.cardBody}</p>
          </Card>
        </Group>
      ))}
    </Stack>
  ),
};

/**
 * `Card` is the surface `StateSlot` renders into, so a reviewer should see the
 * two together at the density `StateSlot` defaults to.
 */
export const AsAStateSurface: RenderedStory = {
  name: 'As the surface a state is rendered into',
  render: () => (
    <Card>
      <h3 style={{ margin: 0, fontSize: '1.125rem' }}>{sampleText.en.cardTitle}</h3>
      <ProgressLike />
    </Card>
  ),
};

function ProgressLike() {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-1)',
        fontSize: '0.875rem',
        color: 'var(--color-ink-soft)',
      }}
    >
      <span>{sampleText.en.progressLabel}</span>
      <div
        role="progressbar"
        aria-label={sampleText.en.progressLabel}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={63}
        aria-valuetext="63%"
        style={{
          blockSize: '0.75rem',
          borderRadius: 'var(--radius-s)',
          backgroundColor: 'var(--color-surface-2)',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            blockSize: '100%',
            inlineSize: '63%',
            backgroundColor: 'var(--color-water)',
            borderRadius: 'inherit',
          }}
        />
      </div>
    </div>
  );
}
