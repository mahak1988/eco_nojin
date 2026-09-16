# Security Policy — Eco Nojin

## Protected by

- **WAF** (Layer 1): SQLi, XSS, path traversal, command injection, SSRF, scanner detection with normalization against encoding bypasses
- **Rate Limiter** (Layer 2): Per-IP (120/min) and per-auth-endpoint (10/min) budgets with Redis + in-memory fallback
- **Anomaly Detector** (Layer 9): Sliding behavioral profile per IP (volume, 4xx ratio, entropy)
- **Honeypot** (Layer 8): 7 trap paths, 24-hour auto-block on hit
- **Circuit Breaker** (Layer 7): Auto-block after 5 WAF blocks in 60 seconds
- **CSRF Protection** (Layer 4): Token required on state-changing requests (Bearer-exempt)
- **Security Headers** (Layer 3): CSP, HSTS, frame deny, referrer policy, permissions policy
- **HTTPS Redirect**: Enforced in production
- **Audit Logging** (Layer 11): All auth/security decisions logged with local JSONL fallback
- **Post-Quantum Readiness** (Layer 6): CRYSTALS-Kyber/Dilithium when liboqs available

## Security Contacts

- **Report vulnerabilities**: security@econojin.ir (PGP key required)
- **Response SLA**: Critical ≤ 4h, High ≤ 24h, Medium ≤ 7d
- **Disclosure**: Responsible disclosure preferred; coordinated release with reporter

## Policy

- No synthetic/fabricated data in any API response
- All secrets stored in environment variables, never in code
- All SQL queries use parameterized bindings
- All user input validated via Pydantic schemas before processing
- JWT tokens: short-lived access (≤15min) + long-lived refresh with rotation
- Cookie-based sessions: HttpOnly + Secure + SameSite=Strict
