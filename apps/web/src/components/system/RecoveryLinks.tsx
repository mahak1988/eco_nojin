import { Link } from '@/i18n/navigation';

export interface RecoveryLinkItem {
  href: string;
  label: string;
  detail?: string;
  token?: string;
}

export function RecoveryLinks({
  links,
  heading,
  headingId,
  viewLabel,
}: {
  links: readonly RecoveryLinkItem[];
  heading: string;
  headingId: string;
  viewLabel: string;
}) {
  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId} className="field-label">
        {heading}
      </h2>
      <ul className="mt-3 space-y-2">
        {links.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className="card flex flex-wrap items-center justify-between gap-3 p-4 hover:border-forest"
            >
              <span className="min-w-0">
                <span className="block text-sm font-semibold text-ink">{link.label}</span>
                {link.detail ? (
                  <span className="mt-1 block text-xs text-ink-soft">{link.detail}</span>
                ) : null}
              </span>
              <span className="flex shrink-0 items-center gap-3">
                {link.token ? (
                  <code className="num text-xs text-ink-faint">{link.token}</code>
                ) : null}
                <span aria-hidden="true" className="text-sm text-ink-faint">
                  →
                </span>
                <span className="sr-only">{viewLabel}</span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
