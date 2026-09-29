import type { HTMLAttributes, ReactNode } from 'react';

/**
 * Optional localized strings for the provenance popover.
 * When omitted, the popover renders raw, locale-neutral values only —
 * no hard-coded copy ever lives in this component (Design System §5.2).
 */
export interface ProvenanceStampLabels {
  heading?: string;
  source?: string;
  method?: string;
  confidence?: string;
  observedAt?: string;
  verified?: string;
  unverified?: string;
}

interface ProvenanceStampProps extends HTMLAttributes<HTMLSpanElement> {
  source: string;
  label?: ReactNode;
  children?: ReactNode;
  verified?: boolean;
  timestamp?: string;
  method?: string;
  /** Model confidence in the [0, 1] range, surfaced inside the popover. */
  modelConfidence?: number;
  /** Localized popover strings supplied by the page that owns the translations. */
  labels?: ProvenanceStampLabels;
}

export function ProvenanceStamp({
  source,
  label,
  children,
  verified,
  timestamp,
  method,
  modelConfidence,
  labels,
  className = '',
  ...props
}: ProvenanceStampProps) {
  const hasDetails = verified !== undefined || timestamp || method || modelConfidence !== undefined;
  const verifiedText = verified
    ? (labels?.verified ?? 'verified')
    : (labels?.unverified ?? 'unverified');
  const confidence = modelConfidence === undefined ? null : `${Math.round(modelConfidence * 100)}%`;

  return (
    <span
      title={source}
      className={`chip group relative ${className}`}
      data-provenance={source}
      {...props}
    >
      <button
        type="button"
        aria-label={source}
        className="grid size-3 shrink-0 cursor-help place-items-center rounded-full text-current transition-micro focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--focus)]"
      >
        <svg aria-hidden="true" width="10" height="10" viewBox="0 0 12 12" fill="none">
          <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.4" />
          <path d="M6 3.2v5.6M3.2 6h5.6" stroke="currentColor" strokeWidth="1.2" />
        </svg>
      </button>
      {label ?? children}
      {hasDetails && (
        <>
          {verified !== undefined && (
            <span className="ms-1 inline-flex" role="img" aria-label={verifiedText}>
              {verified ? '✓' : '✗'}
            </span>
          )}
          {timestamp && (
            <span className="num ms-1 text-[10px] opacity-70">
              {new Date(timestamp).toLocaleDateString()}
            </span>
          )}
          {method && <span className="ms-1 text-[10px] opacity-70">· {method}</span>}
        </>
      )}

      {/* Living Terrain provenance popover — reveal on hover or keyboard focus (§5.2) */}
      <span
        role="tooltip"
        className="pointer-events-none invisible absolute bottom-full start-1/2 z-50 mb-2 flex w-max max-w-[18rem] -translate-x-1/2 translate-y-1 flex-col gap-1.5 rounded-[var(--radius-m)] border border-[var(--line-strong)] bg-[var(--surface)] p-3 text-xs text-[var(--ink)] opacity-0 shadow-[var(--shadow-pop)] transition-structural group-hover:visible group-hover:translate-y-0 group-hover:opacity-100 group-focus-within:visible group-focus-within:translate-y-0 group-focus-within:opacity-100 rtl:translate-x-1/2"
      >
        <span className="flex items-center justify-between gap-3 border-b border-[var(--line)] pb-1.5">
          <span className="flex min-w-0 items-center gap-1.5">
            <span
              className="status-dot"
              data-state={verified === false ? 'warn' : 'ok'}
              aria-hidden="true"
            />
            <span className="truncate text-[0.7rem] font-semibold text-[var(--ink)]">
              {labels?.heading ?? source}
            </span>
          </span>
          {verified !== undefined && (
            <span
              className={verified ? 'text-[var(--forest)]' : 'text-[var(--copper)]'}
              aria-hidden="true"
            >
              {verified ? '✓' : '✗'}
            </span>
          )}
        </span>
        <span className="flex flex-col gap-1 text-[0.7rem] text-[var(--ink-soft)]">
          {labels?.heading && (
            <span className="flex items-center justify-between gap-3">
              {labels.source && <span className="font-medium">{labels.source}</span>}
              <span className="num truncate">{source}</span>
            </span>
          )}
          {method && (
            <span className="flex items-center justify-between gap-3">
              {labels?.method && <span className="font-medium">{labels.method}</span>}
              <span className="num">{method}</span>
            </span>
          )}
          {confidence && (
            <span className="flex items-center justify-between gap-3">
              {labels?.confidence && <span className="font-medium">{labels.confidence}</span>}
              <span className="num">{confidence}</span>
            </span>
          )}
          {timestamp && (
            <span className="flex items-center justify-between gap-3">
              {labels?.observedAt && <span className="font-medium">{labels.observedAt}</span>}
              <span className="num">{new Date(timestamp).toLocaleString()}</span>
            </span>
          )}
        </span>
      </span>
    </span>
  );
}
