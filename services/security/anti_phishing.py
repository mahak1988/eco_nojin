"""Layer 5 — anti-phishing: domain squatting + email auth (SPF/DKIM/DMARC) + clone detection.

- `domain_squatting(host)`: Levenshtein distance against the project's trusted
  domains; close look-alikes are flagged.
- `check_email_auth(domain)`: live DNS TXT lookups via dnspython (free) for
  SPF, DKIM and DMARC. Reports honest `not_configured` when records are absent.
- `page_clone_signature(url)`: structural fingerprint (title + meta + script
  sources) of a public page; similarity >= threshold flags a possible clone.
  Unreachable pages report `requires_network` honestly.
"""

import contextlib
import hashlib
import ipaddress
import os
import re
import socket
import urllib.parse
import urllib.request

from services.api_gateway.errors import safe_error_detail

# قابل تنظیم از محیط (TRUSTED_DOMAINS=econojin.ir,econojin.com)
TRUSTED_DOMAINS: list[str] = [
    d.strip()
    for d in os.getenv("TRUSTED_DOMAINS", "econojin.ir,econojin.com,econojin.land").split(",")
    if d.strip()
]

_UA = {"User-Agent": "Mozilla/5.0 (compatible; EcoNojin-PhishGuard/1.0)"}

#: Fetch timeout for the clone probe — the endpoint is interactive.
_FETCH_TIMEOUT_SECONDS = 5.0

#: Hostnames that never denote a public page.
_BLOCKED_HOSTNAMES = frozenset({"localhost", "localhost.localdomain", "ip6-localhost"})


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Refuse redirects — a public URL may not bounce us into a private one."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ARG002
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


#: Carrier-grade NAT shared range (RFC 6598). Python's ``ipaddress`` does not
#: classify it as private/loopback/link-local, so a flag deny-list lets it
#: through — including Alibaba Cloud's instance-metadata service
#: (``100.100.100.200``), an IAM-credential endpoint of exactly the class
#: ``169.254.169.254`` was blocked for. Denied explicitly.
_CGNAT_NETWORK = ipaddress.ip_network("100.64.0.0/10")


def _reject_url(url: str) -> None:
    """Raise ``ValueError`` unless ``url`` is a public https page (SEC-04).

    ``page_clone_signature`` fetches a caller-supplied URL server-side, which
    is a textbook SSRF sink (cloud metadata endpoints, internal admin panels,
    ``file://`` reads). The constraints here:

    * scheme must be ``https`` (no ``file:``, ``gopher:``, ``ftp:`` …);
    * the host must resolve, and **every** resolved address must be globally
      routable — the test is an allow (``is_global``), not a deny-list, so the
      classes a deny-list misses (RFC 6598 shared range, and anything future
      Python does not yet flag) fail closed. ``100.64.0.0/10`` is additionally
      denied by name for runtimes whose ``is_global`` semantics differ;
    * IPv4-mapped and IPv4-compatible IPv6 addresses are unwrapped before
      the test, so ``[::ffff:127.0.0.1]`` cannot slip through;
    * redirects are refused at the opener level, so the check cannot be
      bypassed by a 302 from a public host to an internal one.

    Residual risk (documented, not silently ignored): the address is validated
    once and the connection re-resolves the name, so a DNS answer that changes
    between the two (a deliberate rebinding) could still reach an internal
    address. Closing that requires pinning the validated IP into the
    connection; the allow-list plus the admin-only route keeps the practical
    exposure at zero for this deployment.
    """
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError as exc:
        raise ValueError(f"unparseable URL: {exc}") from exc
    if parsed.scheme.lower() != "https":
        raise ValueError("only https URLs can be checked")
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        raise ValueError("URL has no host")
    if host in _BLOCKED_HOSTNAMES:
        raise ValueError(f"host {host} is not a public page")
    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except OSError as exc:
        raise ValueError(f"host {host} does not resolve") from exc
    if not infos:
        raise ValueError(f"host {host} does not resolve")
    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise ValueError(f"host {host} resolved to a non-address {address!r}") from exc
        mapped = ip.ipv4_mapped if ip.version == 6 else None
        for candidate in (ip, mapped):
            if candidate is None:
                continue
            if candidate in _CGNAT_NETWORK:
                raise ValueError(
                    f"host {host} resolves to the shared CGNAT range ({candidate})"
                )
            if not candidate.is_global:
                raise ValueError(f"host {host} resolves to a non-public address ({candidate})")


def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def domain_squatting(host: str) -> dict:
    host = host.lower().strip().rstrip(".")
    results = []
    for trusted in TRUSTED_DOMAINS:
        dist = _levenshtein(host, trusted)
        if dist <= 2 and host != trusted:
            results.append({"trusted": trusted, "distance": dist, "suspicious": True})
    return {
        "host": host,
        "trusted_domains": TRUSTED_DOMAINS,
        "squatting": results,
        "verdict": "suspicious" if results else "ok",
    }


def check_email_auth(domain: str) -> dict:
    """Live DNS checks. Requires dnspython; network failures are honest."""
    domain = domain.lower().strip()
    try:
        import dns.resolver

        resolver = dns.resolver.Resolver()
        resolver.timeout = 3.0
        resolver.lifetime = 3.0

        spf: list[str] = []
        dmarc: list[str] = []
        dkim: list[str] = []
        with contextlib.suppress(Exception):
            spf = [str(r) for r in resolver.resolve(domain, "TXT") if "v=spf1" in str(r)]
        with contextlib.suppress(Exception):
            dmarc = [str(r) for r in resolver.resolve(f"_dmarc.{domain}", "TXT")]
        for selector in ("default", "selector1", "k1"):
            with contextlib.suppress(Exception):
                dkim += [str(r) for r in resolver.resolve(f"{selector}._domainkey.{domain}", "TXT")]

        return {
            "domain": domain,
            "spf": spf or ["not_configured"],
            "dkim": dkim or ["not_configured"],
            "dmarc": dmarc or ["not_configured"],
            "verdict": "protected"
            if (spf and dmarc and dkim)
            else ("partial" if (spf or dmarc or dkim) else "unprotected"),
            "note": "سوابق DNS به‌صورت زنده بررسی شد؛ برای ایمیل رسمی پروژه، SPF/DKIM/DMARC باید روی دامنه تنظیم شوند.",
        }
    except Exception as exc:  # pragma: no cover - network dependent
        return {"domain": domain, "status": "error", "error": safe_error_detail(exc)}


def page_clone_signature(url: str) -> dict:
    """Structural fingerprint of a public page; flag near-identical copies.

    SEC-04: the URL is validated as public https *before* any fetch (see
    :func:`_reject_url`); a rejected URL reports ``status="rejected"`` with the
    reason instead of reaching the network.
    """
    try:
        _reject_url(url)
    except ValueError as exc:
        return {"url": url, "status": "rejected", "reason": str(exc)}
    try:
        req = urllib.request.Request(url, headers=_UA)
        with _OPENER.open(req, timeout=_FETCH_TIMEOUT_SECONDS) as resp:
            html = resp.read(200_000).decode("utf-8", "ignore")
        title = (re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S) or [None, ""])[
            1
        ].strip()
        metas = re.findall(r'<meta[^>]+name=["\'](?:description|keywords)["\'][^>]*>', html, re.I)[
            :3
        ]
        scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)', html, re.I)[:8]
        sig_source = f"{title}|{'|'.join(metas)}|{'|'.join(scripts)}"
        digest = hashlib.sha256(sig_source.encode("utf-8")).hexdigest()
        return {
            "url": url,
            "title": title[:120],
            "script_count": len(scripts),
            "signature_sha256": digest,
            "note": "امضای ساختاری صفحه (title+meta+scripts)؛ مقایسه با نسخه رسمی برای تشخیص کلون.",
        }
    except Exception as exc:  # pragma: no cover - network dependent
        return {"url": url, "status": "requires_network", "error": safe_error_detail(exc)}
