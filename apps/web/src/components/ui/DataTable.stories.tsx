import type { Meta, StoryObj } from '@storybook/react-vite';
import { useState } from 'react';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group, Scroll, Stack } from '../../../.storybook/states';
import { Badge } from './Badge';
import { type Column, DataTable, type SortDirection } from './DataTable';

interface Row {
  id: string;
  site: string;
  ndvi: number;
  moisture: number;
  state: 'verified' | 'pending' | 'offline';
}

const ROWS: readonly Row[] = [
  { id: 'r-1', site: 'Urmia lake north', ndvi: 0.62, moisture: 41.8, state: 'verified' },
  { id: 'r-2', site: 'Zayandeh Rud', ndvi: 0.38, moisture: 12.4, state: 'pending' },
  { id: 'r-3', site: 'Alborz ridge', ndvi: 0.81, moisture: 55.1, state: 'verified' },
  { id: 'r-4', site: 'Dasht-e Kavir', ndvi: 0.19, moisture: 4.2, state: 'offline' },
];

const TONE: Record<Row['state'], 'success' | 'warn' | 'bad'> = {
  verified: 'success',
  pending: 'warn',
  offline: 'bad',
};

const COLUMNS: readonly Column<Row>[] = [
  { key: 'site', header: sampleText.en.tableHeaderSite, sortable: true },
  { key: 'ndvi', header: sampleText.en.tableHeaderNdvi, numeric: true, sortable: true },
  { key: 'moisture', header: sampleText.en.tableHeaderMoisture, numeric: true, sortable: true },
  {
    key: 'state',
    header: 'State',
    render: (row) => <Badge tone={TONE[row.state]}>{row.state}</Badge>,
  },
];

/**
 * The meta is annotated rather than `satisfies`-ed because `DataTable` is
 * generic: without the row type the meta resolves to `DataTable<unknown>` and
 * every `Column<Row>` in this file is a type error. Naming the type once here is
 * what lets a real column definition be written, which is the thing worth
 * showing.
 */
const meta: Meta<typeof DataTable<Row>> = {
  title: 'Data/DataTable',
  component: DataTable,
  parameters: { layout: 'fullscreen' },
};

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
 * Unsorted, uncontrolled. The caption is a required prop: a table without one has
 * no accessible name, and the source path is rendered inside it so a reader can
 * ask the gateway the same question the page did.
 */
export const Default: Story = {
  args: {
    columns: COLUMNS,
    rows: ROWS,
    rowKey: (row) => row.id,
    caption: sampleText.en.tableCaption,
    captionExtra: <span className="num">{sampleText.en.tableSource}</span>,
  },
};

/**
 * Sort held by the caller.
 *
 * The sort state living outside the component is the decision worth reviewing: a
 * table driven by a URL query stays shareable, and `aria-sort` on the header is
 * what announces it. Storybook's `args` cannot carry a live updater, so this
 * story owns the state and wires `onSortChange` itself.
 */
export const ControlledSort: RenderedStory = {
  name: 'Sort held by the caller — aria-sort follows',
  render: function ControlledSortStory() {
    const [sort, setSort] = useState<{ key: string; direction: SortDirection } | null>({
      key: 'moisture',
      direction: 'ascending',
    });
    return (
      <Stack>
        <Group label="sorted by the caller">
          <Scroll>
            <DataTable
              columns={COLUMNS}
              rows={ROWS}
              rowKey={(row) => row.id}
              caption={sampleText.en.tableCaption}
              sort={sort}
              onSortChange={(key, direction) => setSort({ key, direction })}
            />
          </Scroll>
        </Group>
      </Stack>
    );
  },
};

/**
 * The three densities. `dense` is the step that has to stay readable at the
 * smallest body size on a phone, which is the whole reason the scale exists.
 */
export const Densities: RenderedStory = {
  name: 'Densities — cozy, compact, dense',
  render: () => (
    <Stack>
      {(['cozy', 'compact', 'dense'] as const).map((density) => (
        <Group key={density} label={density}>
          <Scroll>
            <DataTable
              columns={COLUMNS}
              rows={ROWS}
              rowKey={(row) => row.id}
              caption={sampleText.en.tableCaption}
              density={density}
            />
          </Scroll>
        </Group>
      ))}
    </Stack>
  ),
};

/**
 * No rows. The empty cell spans every column and the label is a prop, so a page
 * that has not translated it renders an empty cell rather than English.
 */
export const Empty: Story = {
  name: 'Empty — the label is a prop',
  args: {
    columns: COLUMNS,
    rows: [],
    rowKey: (row) => row.id,
    caption: sampleText.en.tableCaption,
    emptyLabel: sampleText.en.tableEmpty,
  },
};

/**
 * The alignment frame. `align` defaults to `end` for a `numeric` column, and
 * under `dir="rtl"` that has to be the *start* of the reading direction. Switch
 * the toolbar to `fa`: a table whose numbers still hug the physical right edge
 * is a bug this story is here to surface.
 */
export const AlignmentInRtl: RenderedStory = {
  name: 'Alignment under RTL — numeric columns must hug the reading end',
  parameters: { ecoLocale: 'fa' },
  render: () => (
    <Scroll>
      <DataTable
        columns={COLUMNS}
        rows={ROWS}
        rowKey={(row) => row.id}
        caption={sampleText.fa.tableCaption}
      />
    </Scroll>
  ),
};

/** The five states, with a filled table as the content. */
export const States: RenderedStory = {
  name: 'The five states, through StateSlot',
  render: () => (
    <FiveStates title="DataTable in each of the five states" action>
      <Scroll>
        <DataTable
          columns={COLUMNS}
          rows={ROWS}
          rowKey={(row) => row.id}
          caption={sampleText.en.tableCaption}
        />
      </Scroll>
    </FiveStates>
  ),
};
