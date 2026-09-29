import type { Meta, StoryObj } from '@storybook/react-vite';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group, Stack } from '../../../.storybook/states';
import { Breadcrumb, type Crumb, Pagination } from './Navigation';

const meta = {
  title: 'Navigation/Navigation',
  component: Breadcrumb,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Breadcrumb>;

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

const CRUMBS: readonly Crumb[] = [
  { href: '/en', label: sampleText.en.breadcrumbHome },
  { href: '/en/system', label: sampleText.en.breadcrumbSystem },
  { href: '/en/system/measurements', label: sampleText.en.breadcrumbCurrent },
];

/**
 * The last crumb is text with `aria-current="page"`, not a link. A link to the
 * page you are already on invites a pointless request and tells a screen reader
 * there is somewhere to go.
 */
export const BreadcrumbTrail: Story = {
  name: 'Breadcrumb',
  render: () => (
    <Stack>
      <Group label="breadcrumb">
        <Breadcrumb items={CRUMBS} label={sampleText.en.breadcrumbCurrent} />
      </Group>
      <Group label="breadcrumb with the current label overridden">
        <Breadcrumb items={CRUMBS} label={sampleText.en.breadcrumbCurrent} currentLabel="Site 14" />
      </Group>
      <Group label="a single crumb — no separator, and nothing to link back to">
        <Breadcrumb items={[CRUMBS[2]]} label={sampleText.en.breadcrumbCurrent} />
      </Group>
    </Stack>
  ),
};

/**
 * The separator is a `/` inside an `aria-hidden` span and the list is a flex row,
 * so it mirrors under RTL without a second rule. Switch to `fa` to see that the
 * trail reads right-to-left with the current page on the left.
 */
export const BreadcrumbInRtl: Story = {
  name: 'Breadcrumb under RTL',
  parameters: { ecoLocale: 'fa' },
  render: () => (
    <Breadcrumb
      items={[
        { href: '/fa', label: sampleText.fa.breadcrumbHome },
        { href: '/fa/system', label: sampleText.fa.breadcrumbSystem },
        { href: '/fa/system/measurements', label: sampleText.fa.breadcrumbCurrent },
      ]}
      label={sampleText.fa.breadcrumbCurrent}
    />
  ),
};

/** Middle page, so both `rel="prev"` and `rel="next"` are real links. */
export const PaginationMiddle: Story = {
  name: 'Pagination — page 3 of 7',
  render: () => (
    <Pagination
      page={2}
      pageCount={7}
      hrefFor={(page) => `/en/system/measurements?page=${page + 1}`}
      label={sampleText.en.paginationLabel}
      previousLabel={sampleText.en.paginationPrevious}
      nextLabel={sampleText.en.paginationNext}
    />
  ),
};

/**
 * The first and last pages. The missing direction renders a `<span
 * aria-disabled>` rather than a dead link, so there is no focus stop and nothing
 * to activate.
 */
export const PaginationEdges: Story = {
  name: 'Pagination — first and last page',
  render: () => (
    <Stack>
      <Group label="page 1">
        <Pagination
          page={0}
          pageCount={7}
          hrefFor={(page) => `/en/system/measurements?page=${page + 1}`}
          label={sampleText.en.paginationLabel}
          previousLabel={sampleText.en.paginationPrevious}
          nextLabel={sampleText.en.paginationNext}
        />
      </Group>
      <Group label="page 7">
        <Pagination
          page={6}
          pageCount={7}
          hrefFor={(page) => `/en/system/measurements?page=${page + 1}`}
          label={sampleText.en.paginationLabel}
          previousLabel={sampleText.en.paginationPrevious}
          nextLabel={sampleText.en.paginationNext}
        />
      </Group>
      <Group label="a single page — the control renders nothing at all">
        <span style={{ color: 'var(--color-ink-faint)' }}>—</span>
      </Group>
    </Stack>
  ),
};

/** Persian labels, where the page numbers must still read left to right. */
export const PaginationInRtl: Story = {
  name: 'Pagination under RTL',
  parameters: { ecoLocale: 'fa' },
  render: () => (
    <Pagination
      page={2}
      pageCount={7}
      hrefFor={(page) => `/fa/system/measurements?page=${page + 1}`}
      label={sampleText.fa.paginationLabel}
      previousLabel={sampleText.fa.paginationPrevious}
      nextLabel={sampleText.fa.paginationNext}
    />
  ),
};

/** The five states, with the trail as the content. */
export const States: Story = {
  name: 'The five states, through StateSlot',
  render: () => (
    <FiveStates title="Breadcrumb in each of the five states">
      <Breadcrumb items={CRUMBS} label={sampleText.en.breadcrumbCurrent} />
    </FiveStates>
  ),
};
