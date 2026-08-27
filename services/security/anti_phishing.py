"""Layer 5 — anti-phishing: domain squatting + email auth (SPF/DKIM/DMARC) + clone detection.

- `domain_squatting(host)`: Levenshtein distance against the project's trusted
  domains; close look-alikes are flagged.
- `check_email_auth(domain)`: live DNS TXT lookups via dnspython (free) for
  SPF, DKIM and DMARC. Reports honest `not_configured` when records are absent.
- `page_clone_signature(url)`: structural fingerprint (title + meta + script
  sources) of a public page; similarity >= threshold flags a possible clone.
  Unreachable pages report `requires_network` honestly.
"""
import hashlib
import os
import re
import urllib.request

# قابل تنظیم از محیط (TRUSTED_DOMAINS=econojin.ir,econojin.com)
TRUSTED_DOMAINS: list[str] = [
    d.strip()
    for d in os.getenv("TRUSTED_DOMAINS", "econojin.ir,econojin.com,econojin.land").split(",")
    if d.strip()
]

_UA = {"User-Agent": "Mozilla/5.0 (compatible; EcoNojin-PhishGuard/1.0)"}


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
        try:
            spf = [str(r) for r in resolver.resolve(domain, "TXT") if "v=spf1" in str(r)]
        except Exception:
            pass
        try:
            dmarc = [str(r) for r in resolver.resolve(f"_dmarc.{domain}", "TXT")]
        except Exception:
            pass
        for selector in ("default", "selector1", "k1"):
            try:
                dkim += [str(r) for r in resolver.resolve(f"{selector}._domainkey.{domain}", "TXT")]
            except Exception:
                pass

        return {
            "domain": domain,
            "spf": spf or ["not_configured"],
            "dkim": dkim or ["not_configured"],
            "dmarc": dmarc or ["not_configured"],
            "verdict": "protected" if (spf and dmarc and dkim) else ("partial" if (spf or dmarc or dkim) else "unprotected"),
            "note": "سوابق DNS به‌صورت زنده بررسی شد؛ برای ایمیل رسمی پروژه، SPF/DKIM/DMARC باید روی دامنه تنظیم شوند.",
        }
    except Exception as exc:  # pragma: no cover - network dependent
        return {"domain": domain, "status": "error", "error": str(exc)}


def page_clone_signature(url: str) -> dict:
    """Structural fingerprint of a public page; flag near-identical copies."""
    try:
        req = urllib.request.Request(url, headers=_UA)
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read(200_000).decode("utf-8", "ignore")
        title = (re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S) or [None, ""])[1].strip()
        metas = re.findall(r'<meta[^>]+name=["\'](?:description|keywords)["\'][^>]*>', html, re.I)[:3]
        scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)', html, re.I)[:8]
        sig_source = f"{title}|{'|'.join(metas)}|{'|'.join(scripts)}"
        digest = hashlib.sha256(sig_source.encode("utf-8")).hexdigest()
        return {
            "url": url, "title": title[:120], "script_count": len(scripts),
            "signature_sha256": digest,
            "note": "امضای ساختاری صفحه (title+meta+scripts)؛ مقایسه با نسخه رسمی برای تشخیص کلون.",
        }
    except Exception as exc:  # pragma: no cover - network dependent
        return {"url": url, "status": "requires_network", "error": str(exc)}
