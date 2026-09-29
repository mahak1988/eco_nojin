import type { Meta, StoryObj } from '@storybook/react-vite';
import { useState } from 'react';
import { sampleText } from '../../../.storybook/fixtures';
import { Group } from '../../../.storybook/states';
import { Button } from './Button';
import { ErrorBoundary } from './ErrorBoundary';

const meta = {
  title: 'Overlays/ErrorBoundary',
  component: ErrorBoundary,
  parameters: { layout: 'fullscreen' },
} satisfies Meta<typeof ErrorBoundary>;

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

/** The happy path: the boundary renders its children and adds nothing to them. */
export const Children: Story = {
  name: 'No error — the children, unchanged',
  args: { children: <p style={{ margin: 0 }}>{sampleText.en.cardBody}</p> },
};

/**
 * The built-in fallback.
 *
 * Read the copy: `Something went wrong`, `We encountered an unexpected error…`
 * and the `Try again` label are literals inside the component, in a library whose
 * stated rule is that it carries no translatable string. Outside development the
 * error detail is dropped, so a Persian page renders three sentences of English in
 * the one place the reader has already been told something went wrong. Reported
 * rather than worked around: the next two stories are the two supported ways to
 * replace it, and this one exists to show what the default costs.
 */
export const DefaultFallback: RenderedStory = {
  name: 'Thrown error — the built-in fallback, which is hard-coded English',
  args: { children: <Explode /> },
  render: (args) => (
    <ErrorBoundary {...args}>
      <Explode />
    </ErrorBoundary>
  ),
};

/** `fallbackRender`, which is how a page replaces that copy with translated text. */
export const CustomFallbackRender: RenderedStory = {
  name: 'fallbackRender — translated copy and a retry composed from Button',
  args: { children: <Explode /> },
  render: () => (
    <ErrorBoundary fallbackRender={() => <TranslatedFallback />}>
      <Explode />
    </ErrorBoundary>
  ),
};

/** `fallback`, a ready-made node, for the cases a render function does not help. */
export const CustomFallbackNode: RenderedStory = {
  name: 'fallback — a ready-made node',
  args: { children: <Explode /> },
  render: () => (
    <ErrorBoundary fallback={<TranslatedFallback />}>
      <Explode />
    </ErrorBoundary>
  ),
};

/**
 * The retry path. The child throws on its first render and resolves on the second,
 * which is the sequence `reset` exists for — a boundary that cannot be reset is a
 * page the reader has to reload.
 */
export const Retry: RenderedStory = {
  name: 'Retry — the child stops throwing and the boundary clears',
  args: { children: <Explode /> },
  render: () => (
    <ErrorBoundary fallbackRender={() => <TranslatedFallback />}>
      <FlakyChild />
    </ErrorBoundary>
  ),
};

/** The same frame, pinned to Persian, for the copy a reader would actually see. */
export const RetryInPersian: RenderedStory = {
  name: 'Retry, in Persian',
  parameters: { ecoLocale: 'fa' },
  render: () => (
    <ErrorBoundary
      fallbackRender={() => (
        <TranslatedFallback
          title={sampleText.fa.boundaryTitle}
          body={sampleText.fa.boundaryBody}
          action={sampleText.fa.boundaryRetry}
        />
      )}
    >
      <FlakyChild />
    </ErrorBoundary>
  ),
};

/** A child that always throws, so the fallback is what a reviewer sees. */
function Explode(): React.ReactNode {
  throw new Error('readings/2026-08-12: gateway returned 503 for site-0014');
}

/** Throws on the first render only, so `reset` has something to recover. */
function FlakyChild() {
  const [failed, setFailed] = useState(true);
  if (failed) {
    setFailed(false);
    throw new Error('readings/2026-08-12: gateway returned 503 for site-0014');
  }
  return (
    <p style={{ margin: 0, color: 'var(--color-ink)' }} role="status">
      {sampleText.en.progressDetail}
    </p>
  );
}

/**
 * The translated fallback, which is the shape the copy rule expects. It lives in
 * the story rather than in the component because a component library that carried
 * it would be carrying product copy.
 */
function TranslatedFallback({
  title = sampleText.en.boundaryTitle,
  body = sampleText.en.boundaryBody,
  action = sampleText.en.boundaryRetry,
}: {
  title?: string;
  body?: string;
  action?: string;
}) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 'var(--space-4)',
        padding: 'var(--space-8)',
        background: 'var(--color-surface)',
        border: '1px solid var(--color-line)',
        borderRadius: 'var(--radius-16)',
        textAlign: 'center',
      }}
      role="alert"
    >
      <h2 style={{ margin: 0, fontFamily: 'var(--font-display)' }}>{title}</h2>
      <p style={{ margin: 0, maxInlineSize: '28rem', color: 'var(--color-ink-soft)' }}>{body}</p>
      <Group label="the translated retry, composed from Button rather than hard-coded">
        <Button variant="primary">{action}</Button>
      </Group>
    </div>
  );
}
