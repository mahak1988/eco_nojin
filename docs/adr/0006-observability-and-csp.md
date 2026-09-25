# Observability, CSP and RUM

**Status:** Baseline headers and report-only CSP are implemented. Sentry/OpenTelemetry and RUM collection remain environment-gated.

## Security headers

All frontend responses include:

- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Resource-Policy: same-site`
- `Permissions-Policy` with a minimal default
- `Content-Security-Policy-Report-Only` with a baseline policy

`Strict-Transport-Security` is added only in production. The CSP report endpoint is `/api/csp-report` and intentionally discards the report body; it does not log CSP samples or user data.

The report-only policy is a rollout gate. It must be reviewed against a production build before enforcement. A global nonce policy is not permitted because it invalidates ISR/CDN caching for dynamic and public pages.

## Observability rules

- Browser telemetry uses the official `web-vitals` library for LCP, CLS and INP.
- The frontend reports vitals to `/api/observability/web-vitals`; the endpoint currently discards payloads until a production sink is configured.
- Release, environment and build hash are required dimensions.
- Form contents, AI prompts, tokens, cookies and payment data are forbidden in telemetry.
- Request IDs are propagated from the BFF but not combined with payload bodies.
- Production alerting covers JS error rate, API failure rate, LCP, CLS and INP.

## Required next gates

1. Configure Sentry or OpenTelemetry Web behind an environment flag.
2. Add RUM sampling and dashboard thresholds.
3. Review the CSP report stream in staging.
4. Switch CSP from report-only to enforce only after violations reach zero and the allowlist is approved.
5. Add Lighthouse CI performance budgets and bundle-size enforcement.
