import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { Group, Stack } from '../../../.storybook/states';
import { Badge } from './Badge';

const meta = {
  title: 'Primitives/Badge',
  component: Badge,
  args: { children: sampleText.en.badgeNeutral },
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Badge>;

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
 * A badge carries a tone, and the tone is a token reference rather than a hex
 * value, so a pill in the dark theme picks up the palette instead of fighting
 * it. The five tones side by side is the frame that proves that.
 */
export const Tones: Story = {
  name: 'Tones — neutral, info, success, warn, bad',
  render: () => (
    <Stack>
      <Group label="tone">
        <div className="eco-row">
          <Badge tone="neutral">{sampleText.en.badgeNeutral}</Badge>
          <Badge tone="info">{sampleText.en.badgeInfo}</Badge>
          <Badge tone="success">{sampleText.en.badgeSuccess}</Badge>
          <Badge tone="warn">{sampleText.en.badgeWarn}</Badge>
          <Badge tone="bad">{sampleText.en.badgeBad}</Badge>
        </div>
      </Group>
      <Group label="tone with the leading dot — decorative, the label carries the meaning">
        <div className="eco-row">
          <Badge tone="neutral" dot>
            {sampleText.en.badgeNeutral}
          </Badge>
          <Badge tone="info" dot>
            {sampleText.en.badgeInfo}
          </Badge>
          <Badge tone="success" dot>
            {sampleText.en.badgeSuccess}
          </Badge>
          <Badge tone="warn" dot>
            {sampleText.en.badgeWarn}
          </Badge>
          <Badge tone="bad" dot>
            {sampleText.en.badgeBad}
          </Badge>
        </div>
      </Group>
    </Stack>
  ),
};

/** The three steps, which is what makes a badge usable in a table cell. */
export const Densities: Story = {
  name: 'Densities — cozy, compact, dense',
  render: () => (
    <Stack>
      {(['cozy', 'compact', 'dense'] as const).map((density) => (
        <Group key={density} label={density}>
          <div className="eco-row">
            <Badge density={density}>{sampleText.en.badgeNeutral}</Badge>
            <Badge density={density} tone="success" dot>
              {sampleText.en.badgeSuccess}
            </Badge>
            <Badge density={density} tone="warn">
              {sampleText.en.badgeWarn}
            </Badge>
          </div>
        </Group>
      ))}
    </Stack>
  ),
};

/**
 * Persian labels. The longer words are the point: `neutral` in English is one
 * short word, and the Persian for "needs review" is three, so this is the frame
 * that shows whether the pill is allowed to grow and whether `white-space:
 * nowrap` fights the inline size.
 */
export const InPersian: Story = {
  name: 'Persian labels',
  parameters: { ecoLocale: 'fa' },
  render: () => (
    <Stack>
      {(['cozy', 'compact', 'dense'] as const).map((density) => (
        <Group key={density} label={density}>
          <div className="eco-row">
            <Badge density={density}>{sampleText.fa.badgeNeutral}</Badge>
            <Badge density={density} tone="success" dot>
              {sampleText.fa.badgeSuccess}
            </Badge>
            <Badge density={density} tone="warn">
              {sampleText.fa.badgeWarn}
            </Badge>
            <Badge density={density} tone="bad">
              {sampleText.fa.badgeBad}
            </Badge>
          </div>
        </Group>
      ))}
    </Stack>
  ),
};
