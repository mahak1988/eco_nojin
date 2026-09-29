'use client';

import { useQuery } from '@tanstack/react-query';
import Image from 'next/image';
import { useTranslations } from 'next-intl';

/**
 * Sponsorship slot. Not an advertisement.
 *
 * Rules this component is built to hold, and which the placement guard test
 * also enforces across the whole tree:
 *   - renders nothing at all when there is no sponsor, not an empty frame
 *   - the disclosure is permanent and unremovable
 *   - no impression, no view tracking, no third-party script, no cookie
 *   - the response carries no user data, so nothing here can be personalised
 *   - fixed height and truncated text, so cumulative layout shift is zero
 *
 * The visual budget (max 12% of a page) lives in
 * services/sponsors/policy.py and is asserted by the Python test suite; this
 * component is written to respect it rather than to re-declare it.
 */

export type SlotPlacement = 'public_services' | 'public_audiences' | 'tool_footer';

export type SlotPayload =
  | { present: false }
  | {
      present: true;
      disclosure: { required: boolean; template_key: string };
      sponsor: {
        name: string;
        name_fa?: string | null;
        url: string;
        logo_url?: string | null;
        tagline?: string | null;
        tagline_fa?: string | null;
        tier: string;
        is_project_funder: boolean;
      };
      expires_on: string;
    };

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export function SponsorSlot({
  placement,
  className,
}: {
  placement: SlotPlacement;
  className?: string;
}) {
  // The catalog holds these two strings at `sponsors.*`, not `sponsors.slot.*`.
  // `check-message-usage.mjs` resolves the namespace from this call, so a `slot`
  // prefix here asked for keys that exist in no catalog and the component would
  // have thrown MISSING_MESSAGE at render time.
  const t = useTranslations('sponsors');
  const locale = useTranslations();

  const { data } = useQuery<SlotPayload>({
    queryKey: ['sponsor-slot', placement],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/v1/sponsors/slot?placement=${placement}`);
      if (!res.ok) return { present: false } as SlotPayload;
      return (await res.json()) as SlotPayload;
    },
    // Content changes only when a sponsorship is activated or expires, so a
    // long stale window is correct and keeps infrastructure cost down.
    staleTime: 900_000,
    gcTime: 3_600_000,
    retry: 1,
  });

  // Nothing renders when there is no sponsor. An empty frame would still cost
  // layout, and a placeholder that later fills is exactly the pattern that
  // becomes programmatic advertising.
  if (!data?.present) return null;

  const isFa = locale.has?.('common.fa') ?? false;
  const name = isFa ? (data.sponsor.name_fa ?? data.sponsor.name) : data.sponsor.name;
  const tagline = isFa ? (data.sponsor.tagline_fa ?? data.sponsor.tagline) : data.sponsor.tagline;

  return (
    <aside
      aria-label={t('region_label')}
      data-testid="sponsor-slot"
      data-placement={placement}
      data-tier={data.sponsor.tier}
      className={[
        'eco-sponsor-slot',
        'flex items-center gap-3 rounded-lg border border-ink/10 bg-ink/[0.02] p-3',
        // Fixed width at every breakpoint. A slot that resizes with content
        // is a cumulative layout shift on every page that carries it.
        'w-full max-w-[240px]',
        className ?? '',
      ].join(' ')}
    >
      {data.sponsor.logo_url ? (
        <Image
          src={data.sponsor.logo_url}
          alt=""
          width={56}
          height={32}
          className="shrink-0 object-contain"
        />
      ) : null}

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">
          <a
            href={data.sponsor.url}
            rel="sponsored noopener noreferrer"
            target="_blank"
            className="hover:underline"
          >
            {name}
          </a>
        </p>
        {tagline ? <p className="truncate text-xs text-ink-soft">{tagline}</p> : null}
      </div>

      {/*
        Disclosure is rendered unconditionally, below the content, and cannot be
        dismissed. `rel="sponsored"` above is the HTML signal that this is
        paid content; this text is the human-readable one. Both are required.
      */}
      <p
        data-testid="sponsor-disclosure"
        className="mt-1 w-full text-[10px] leading-tight text-ink-soft"
      >
        {t('disclosure', { sponsor: name })}
      </p>
    </aside>
  );
}
