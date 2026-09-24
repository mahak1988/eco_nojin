import type { ReactNode, HTMLAttributes } from 'react';

interface ProvenanceStampProps extends HTMLAttributes<HTMLSpanElement> {
  source: string;
  label?: ReactNode;
  children?: ReactNode;
  verified?: boolean;
  timestamp?: string;
  method?: string;
}

export function ProvenanceStamp({
  source,
  label,
  children,
  verified,
  timestamp,
  method,
}: ProvenanceStampProps) {
  const hasDetails = verified !== undefined || timestamp || method;
  
  return (
    <span title={source} className="chip" data-provenance={source}>
      <svg aria-hidden="true" width="10" height="10" viewBox="0 0 12 12" fill="none">
        <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.4" />
        <path d="M6 3.2v5.6M3.2 6h5.6" stroke="currentColor" strokeWidth="1.2" />
      </svg>
      {label ?? children}
      {hasDetails && (
        <>
          {verified !== undefined && (
            <span className="ml-1" aria-label={verified ? 'Verified' : 'Not verified'}>
              {verified ? '✓' : '✗'}
            </span>
          )}
          {timestamp && (
            <span className="ml-1 text-[10px] opacity-70">
              {new Date(timestamp).toLocaleDateString()}
            </span>
          )}
          {method && (
            <span className="ml-1 text-[10px] opacity-70">· {method}</span>
          )}
        </>
      )}
    </span>
  );
}
