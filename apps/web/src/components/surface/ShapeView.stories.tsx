import type { Meta, StoryObj } from '@storybook/react-vite';
import { Group, Stack } from '../../../.storybook/states';
import { ShapeView } from './ShapeView';

/**
 * The one surface component that a Vite preview can render.
 *
 * `EndpointSurface` and `NoJsSearch` are async server components that resolve
 * their copy through `next-intl/server`, so they need the Next request runtime and
 * a real request locale; `ShapeView` is a pure function of the payload and is
 * covered here. The coverage gate in `check-ui-kit.mjs` names both exclusions and
 * why, so they are visible rather than silently skipped.
 */
const meta = {
  title: 'Surfaces/ShapeView',
  component: ShapeView,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof ShapeView>;

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

/** A single object with no array inside it renders as a definition list. */
export const ObjectPayload: Story = {
  name: 'A flat object — a definition list, keys exactly as the gateway sent them',
  args: {
    caption: 'soil profile',
    value: {
      texture: 'silty clay loam',
      organic_carbon_pct: 1.84,
      bulk_density_g_cm3: 1.31,
      notes: null,
    },
  },
};

/**
 * An array of objects becomes a table whose header row is the dataset's own
 * column names. The component never asserts a schema, so a key the server did not
 * send produces no column and a value that is absent produces an em dash.
 */
export const RecordArray: Story = {
  name: 'An array of records — a table built from the payload keys',
  args: {
    caption: 'data',
    value: {
      data: [
        { site: 'Urmia lake north', ndvi: 0.62, moisture: 41.8 },
        { site: 'Zayandeh Rud', ndvi: 0.38, moisture: 12.4 },
        { site: 'Alborz ridge', ndvi: 0.81, moisture: 55.1 },
      ],
    },
  },
};

/** Any of the six conventional row keys is recognised, not just `data`. */
export const AlternativeRowKeys: RenderedStory = {
  name: 'Every recognised row key — data, results, items, rows, records, entries',
  render: () => (
    <Stack>
      {(['data', 'results', 'items', 'rows', 'records', 'entries'] as const).map((key) => (
        <Group key={key} label={key}>
          <ShapeView value={{ [key]: [{ a: 1 }, { a: 2 }] }} />
        </Group>
      ))}
    </Stack>
  ),
};

/** A bare array of scalars renders as a list of `.num` chips. */
export const ScalarArray: Story = {
  name: 'An array of scalars — one chip per value',
  args: { value: [1204.5, 88, 0.075, 'north'] },
};

/** `{}` is a legitimate answer, and renders as an em dash rather than an error. */
export const EmptyObject: Story = {
  name: 'An empty object — a legitimate answer, not a failure',
  args: { value: {} },
};

/** The four values with no shape at all. */
export const ScalarsAndEmpty: RenderedStory = {
  name: 'Scalar, null and empty-array payloads',
  render: () => (
    <Stack>
      <Group label="a number">
        <ShapeView value={1204.5} />
      </Group>
      <Group label="null">
        <ShapeView value={null} />
      </Group>
      <Group label="undefined">
        <ShapeView value={undefined} />
      </Group>
      <Group label="an empty array">
        <ShapeView value={[]} />
      </Group>
      <Group label="a string">
        <ShapeView value="no data published for this contract" />
      </Group>
    </Stack>
  ),
};

/** Nested objects, which recurse into the same two presentations. */
export const Nested: RenderedStory = {
  name: 'Nested objects and arrays',
  render: () => (
    <Stack>
      <Group label="an object holding an array of objects">
        <ShapeView
          value={{
            site: 'Urmia lake north',
            readings: [
              { date: '2026-08-01', ndvi: 0.6 },
              { date: '2026-08-12', ndvi: 0.62 },
            ],
          }}
        />
      </Group>
      <Group label="an array of arrays">
        <ShapeView
          value={[
            [1, 2],
            [3, 4],
          ]}
        />
      </Group>
    </Stack>
  ),
};

/** Persian frame, so the `.num` isolation and the table alignment are reviewable. */
export const InPersian: RenderedStory = {
  name: 'A record array under RTL',
  parameters: { ecoLocale: 'fa' },
  render: () => (
    <ShapeView
      caption="data"
      value={{
        data: [
          { site: 'دریاچه ارومیه شمالی', ndvi: 0.62, moisture: 41.8 },
          { site: 'زاینده‌رود', ndvi: 0.38, moisture: 12.4 },
        ],
      }}
    />
  ),
};
