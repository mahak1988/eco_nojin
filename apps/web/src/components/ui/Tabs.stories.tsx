import type { Meta, StoryObj } from '@storybook/react-vite';
import { useState } from 'react';
import { sampleText } from '../../../.storybook/fixtures';
import { FiveStates, Group, Stack } from '../../../.storybook/states';
import { type TabItem, TabPanel, Tabs } from './Tabs';

const ITEMS: readonly TabItem[] = [
  { id: 'overview', label: sampleText.en.tabsOverview },
  { id: 'measurements', label: sampleText.en.tabsMeasurements, hint: '51' },
  { id: 'history', label: sampleText.en.tabsHistory },
  { id: 'maintenance', label: sampleText.en.tabsLocked, disabled: true },
];

const meta = {
  title: 'Navigation/Tabs',
  component: Tabs,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof Tabs>;

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
 * The keyboard contract is the point of this component: a plain row of buttons
 * puts four stops in the tab order where the WAI-ARIA pattern calls for one.
 * Tab once into the list, then use ←/→ and Home/End. Only the selected tab is in
 * the tab order, and the selection moves with focus.
 */
export const Default: Story = {
  render: function DefaultTabs() {
    const [active, setActive] = useState('overview');
    return (
      <Tabs items={ITEMS} activeId={active} onChange={setActive} label={sampleText.en.tabsLabel}>
        <TabPanel id="overview" activeId={active}>
          <Panel />
        </TabPanel>
        <TabPanel id="measurements" activeId={active}>
          <Panel />
        </TabPanel>
        <TabPanel id="history" activeId={active}>
          <Panel />
        </TabPanel>
      </Tabs>
    );
  },
};

/** The caller-owned panel, which is what `TabPanel` exists for. */
export const CallerOwnedPanel: Story = {
  name: 'Caller-owned panels — TabPanel renders only the active one',
  render: function CallerOwned() {
    const [active, setActive] = useState('measurements');
    return (
      <Tabs items={ITEMS} activeId={active} onChange={setActive} label={sampleText.en.tabsLabel}>
        <TabPanel id="overview" activeId={active}>
          <Panel>{sampleText.en.tabsBody}</Panel>
        </TabPanel>
        <TabPanel id="measurements" activeId={active}>
          <Panel>{sampleText.en.tabsBody}</Panel>
        </TabPanel>
        <TabPanel id="history" activeId={active}>
          <Panel>{sampleText.en.tabsBody}</Panel>
        </TabPanel>
      </Tabs>
    );
  },
};

/** The three densities, which is what keeps a long tab list inside a card. */
export const Densities: Story = {
  name: 'Densities — cozy, compact, dense',
  render: function DensityTabs() {
    const [active, setActive] = useState('overview');
    return (
      <Stack>
        {(['cozy', 'compact', 'dense'] as const).map((density) => (
          <Group key={density} label={density}>
            <Tabs
              items={ITEMS}
              activeId={active}
              onChange={setActive}
              label={sampleText.en.tabsLabel}
              density={density}
            >
              <Panel />
            </Tabs>
          </Group>
        ))}
      </Stack>
    );
  },
};

/**
 * Persian labels at the same density. The `hint` count is rendered through the
 * `.num` rule — tabular digits, isolated from the surrounding RTL text — which is
 * the frame that shows whether a Latin digit in a Persian tab still reads in the
 * right order.
 */
export const InPersian: Story = {
  name: 'Persian labels with a numeric hint',
  parameters: { ecoLocale: 'fa' },
  render: function PersianTabs() {
    const [active, setActive] = useState('overview');
    const faItems: TabItem[] = [
      { id: 'overview', label: sampleText.fa.tabsOverview },
      { id: 'measurements', label: sampleText.fa.tabsMeasurements, hint: '۵۱' },
      { id: 'history', label: sampleText.fa.tabsHistory },
      { id: 'maintenance', label: sampleText.fa.tabsLocked, disabled: true },
    ];
    return (
      <Tabs items={faItems} activeId={active} onChange={setActive} label={sampleText.fa.tabsLabel}>
        <Panel>{sampleText.fa.tabsBody}</Panel>
      </Tabs>
    );
  },
};

/** The five states, with the tab list as the persistent chrome. */
export const States: Story = {
  name: 'The five states, through StateSlot',
  render: function TabsInStates() {
    const [active, setActive] = useState('overview');
    return (
      <FiveStates title="Tabs in each of the five states">
        <Tabs items={ITEMS} activeId={active} onChange={setActive} label={sampleText.en.tabsLabel}>
          <Panel />
        </Tabs>
      </FiveStates>
    );
  },
};

function Panel({ children }: { children?: string }) {
  return (
    <p style={{ margin: 0, color: 'var(--color-ink-soft)' }}>
      {children ?? sampleText.en.tabsBody}
    </p>
  );
}
