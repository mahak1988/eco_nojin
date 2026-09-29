import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { Group, Stack } from '../../../.storybook/states';
import { Accordion, type AccordionItem } from './Accordion';

const meta = {
  title: 'Primitives/Accordion',
  component: Accordion,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Accordion>;

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
 * Fixture data, not product copy. See the note in `Button.stories.tsx` and in
 * `.storybook/labels.ts` for why every literal in a story lives outside the
 * story file.
 */
const ITEMS: readonly AccordionItem[] = [
  {
    id: 'soil',
    title: sampleText.en.soilTitle,
    summary: sampleText.en.soilSummary,
    content: <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>{sampleText.en.soilBody}</p>,
  },
  {
    id: 'water',
    title: sampleText.en.waterTitle,
    summary: sampleText.en.waterSummary,
    content: <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>{sampleText.en.waterBody}</p>,
  },
  {
    id: 'canopy',
    title: sampleText.en.canopyTitle,
    content: (
      <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>{sampleText.en.canopyBody}</p>
    ),
  },
];

const FA_ITEMS: readonly AccordionItem[] = [
  {
    id: 'soil',
    title: sampleText.fa.soilTitle,
    summary: sampleText.fa.soilSummary,
    content: <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>{sampleText.fa.soilBody}</p>,
  },
  {
    id: 'water',
    title: sampleText.fa.waterTitle,
    content: <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>{sampleText.fa.waterBody}</p>,
  },
];

/** Two panels open, the group named, nothing selected. */
export const Default: Story = {
  args: { items: ITEMS, label: sampleText.en.groupLabel, defaultExpanded: ['soil'] },
};

/**
 * The two directions the group can be driven, side by side.
 *
 * `exclusive` matters to a reviewer because a page can be either: a FAQ wants
 * several open, a step-by-step survey wants one.
 */
export const ExclusiveVsMultiple: RenderedStory = {
  name: 'Exclusive vs multiple',
  render: () => (
    <div className="eco-grid">
      <Group label="exclusive">
        <Accordion
          items={ITEMS}
          label={sampleText.en.groupLabel}
          exclusive
          defaultExpanded={['soil']}
        />
      </Group>
      <Group label="multiple (default)">
        <Accordion
          items={ITEMS}
          label={sampleText.en.groupLabel}
          defaultExpanded={['soil', 'water']}
        />
      </Group>
    </div>
  ),
};

/** A disabled trigger must be visibly inert and must not carry `aria-expanded`. */
export const DisabledItem: Story = {
  name: 'A disabled item',
  args: {
    label: sampleText.en.groupLabel,
    items: [
      ...ITEMS.slice(0, 2),
      { id: 'locked', title: sampleText.en.lockedTitle, disabled: true, content: <p>—</p> },
    ],
  },
};

/** The three density steps, which are what make a long FAQ fit a page. */
export const Densities: RenderedStory = {
  name: 'Densities — cozy, compact, dense',
  render: () => (
    <Stack>
      {(['cozy', 'compact', 'dense'] as const).map((density) => (
        <Group key={density} label={density}>
          <Accordion
            items={ITEMS.slice(0, 2)}
            label={sampleText.en.groupLabel}
            density={density}
            defaultExpanded={['soil']}
          />
        </Group>
      ))}
    </Stack>
  ),
};

/**
 * Persian copy at the same density. Switch the toolbar to `fa` and this is the
 * frame that shows whether the trigger's `text-align: start` and the `›` glyph
 * mirror correctly.
 */
export const InPersian: Story = {
  name: 'Persian copy',
  args: { items: FA_ITEMS, label: sampleText.fa.groupLabel, defaultExpanded: ['soil'] },
  parameters: { ecoLocale: 'fa' },
};
