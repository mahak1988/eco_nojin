import type { Meta, StoryObj } from '@storybook/react-vite';
import { useEffect } from 'react';
import { sampleText } from '../../../.storybook/fixtures';
import { Group, Stack } from '../../../.storybook/states';
import { OfflineBanner } from './OfflineBanner';

const meta = {
  title: 'Overlays/OfflineBanner',
  component: OfflineBanner,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof OfflineBanner>;

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
 * The component decides what to show by reading `navigator.onLine` and then
 * listening for `online` / `offline`, so a story cannot pass a prop to get the
 * degraded frame: it has to make the browser report the state it wants. These
 * stories dispatch the same events a real connection change fires, which is the
 * only way to exercise the listener rather than a prop that does not exist.
 *
 * The banner is `position: fixed` at the top of the viewport, so the frame below
 * is page content to show the overlay against.
 */
export const Online: Story = {
  name: 'Online — the banner renders nothing',
  render: function OnlineStory() {
    return (
      <Stack>
        <Group label="page content">
          <p style={{ margin: 0 }}>{sampleText.en.cardBody}</p>
        </Group>
        <OfflineBanner
          message={sampleText.en.offlineMessage}
          reconnectingMessage={sampleText.en.reconnectingMessage}
        />
      </Stack>
    );
  },
};

/** The `offline` event, which is the frame the whole component exists for. */
export const Offline: Story = {
  name: 'Offline — the banner slides in',
  render: function OfflineStory() {
    useNetworkState('offline');
    return (
      <Stack>
        <Group label="page content">
          <p style={{ margin: 0 }}>{sampleText.en.cardBody}</p>
        </Group>
        <OfflineBanner
          message={sampleText.en.offlineMessage}
          reconnectingMessage={sampleText.en.reconnectingMessage}
        />
      </Stack>
    );
  },
};

/**
 * Back online but not yet settled: the banner turns the `water` token rather than
 * disappearing, so the reader is told the connection is being re-established
 * instead of being left to guess why the data stopped updating.
 */
export const Reconnecting: Story = {
  name: 'Reconnecting — online again, still shown',
  render: function ReconnectingStory() {
    useNetworkState('online-after-offline');
    return (
      <Stack>
        <Group label="page content">
          <p style={{ margin: 0 }}>{sampleText.en.cardBody}</p>
        </Group>
        <OfflineBanner
          message={sampleText.en.offlineMessage}
          reconnectingMessage={sampleText.en.reconnectingMessage}
        />
      </Stack>
    );
  },
};

/** Persian copy, which is the frame a translated page would show. */
export const InPersian: Story = {
  name: 'Persian copy, offline',
  parameters: { ecoLocale: 'fa' },
  render: function PersianOffline() {
    useNetworkState('offline');
    return (
      <OfflineBanner
        message={sampleText.fa.offlineMessage}
        reconnectingMessage={sampleText.fa.reconnectingMessage}
      />
    );
  },
};

/**
 * Fires the browser events the component listens for. `offline` is dispatched
 * after mount so the effect has already subscribed, which is the only ordering in
 * which the listener is what makes the frame appear.
 */
function useNetworkState(state: 'offline' | 'online-after-offline') {
  useEffect(() => {
    window.dispatchEvent(new Event('offline'));
    if (state === 'online-after-offline') {
      const timer = window.setTimeout(() => window.dispatchEvent(new Event('online')), 50);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [state]);
}
