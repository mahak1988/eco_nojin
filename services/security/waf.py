"""Layer 1 — WAF ruleset (signature-based).

Scores each request against compiled patterns (SQLi, XSS, path traversal,
command injection, SSRF-ish schemes, scanner user-agents). A request whose
score crosses the threshold is blocked (403) and recorded as a security event.
"""
import re
import time
from typing import Dict, List, Tuple

# rule name -> (compiled regex, weight, block_when_hit)
_RULES: List[Tuple[str, "re.Pattern[str]", int, bool]] = [
    # SQL injection
    ("sqli-union", re.compile(r"(?i)\bunion\s+(all\s+)?select\b"), 40, True),
    ("sqli-select-from", re.compile(r"(?i)\bselect\b.{0,60}\bfrom\b"), 30, True),
    ("sqli-insert", re.compile(r"(?i)\binsert\s+into\b"), 30, True),
    ("sqli-drop", re.compile(r"(?i)\bdrop\s+table\b"), 40, True),
    ("sqli-comment", re.compile(r"(?i)(--\s|/\*!?|#\s)"), 15, False),
    ("sqli-pg-func", re.compile(r"(?i)\b(pg_sleep|information_schema|pg_catalog)\b"), 35, True),
    ("sqli-tautology", re.compile(r"(?i)\b(or|and)\s+\d+\s*=\s*\d+\b"), 25, False),
    # XSS
    ("xss-script", re.compile(r"(?i)<\s*script\b"), 40, True),
    ("xss-handler", re.compile(r"(?i)\bon(error|load|click|mouseover)\s*="), 30, True),
    ("xss-javascript", re.compile(r"(?i)javascript\s*:"), 30, True),
    ("xss-doc-cookie", re.compile(r"(?i)document\.cookie"), 35, True),
    ("xss-iframe", re.compile(r"(?i)<\s*iframe\b"), 25, False),
    # Path traversal
    ("traversal-dotdot", re.compile(r"(?i)(\.\./|\.\.%2f|%2e%2e|\.\.\\)"), 40, True),
    ("traversal-abs", re.compile(r"(?i)(/etc/passwd|/windows/win\.ini|/proc/self)"), 40, True),
    # Command injection
    ("cmdi-shell", re.compile(r"(?i)(;\s*(ls|cat|whoami|id|rm|curl|wget|nc)\b)"), 40, True),
    ("cmdi-subshell", re.compile(r"(\$\(|`[^`]{1,60}`)"), 35, True),
    ("cmdi-pwsh", re.compile(r"(?i)(powershell\s+-|cmd\.exe|bash\s+-c)"), 35, True),
    # SSRF-ish URL schemes
    ("ssrf-scheme", re.compile(r"(?i)\b(file|gopher|dict|ftp)://"), 30, True),
    # Scanner user-agents
    ("scanner-ua", re.compile(r"(?i)(sqlmap|nikto|nmap|nessus|acunetix|openvas|burpsuite)"), 45, True),
]

BLOCK_THRESHOLD = 40


class WafEngine:
    """In-memory WAF. `check` returns (allowed, score, hits, reason)."""

    def __init__(self) -> None:
        self.events: List[Dict] = []

    def check(self, method: str, path: str, query: str, body: str, user_agent: str) -> Tuple[bool, int, List[str], str]:
        """Evaluate one request. Returns (allowed, score, matched_rules, reason)."""
        payload = f"{path} {query} {body}"
        score = 0
        hits: List[str] = []
        for name, pattern, weight, block_when_hit in _RULES:
            if pattern.search(payload) or pattern.search(user_agent):
                score += weight
                hits.append(name)
                if block_when_hit and weight >= BLOCK_THRESHOLD:
                    self.events.append({
                        "ts": time.time(), "method": method, "path": path,
                        "rule": name, "score": score, "decision": "block",
                    })
                    return False, score, hits, f"waf:{name}"
        allowed = score < BLOCK_THRESHOLD
        if not allowed:
            self.events.append({
                "ts": time.time(), "method": method, "path": path,
                "rule": ",".join(hits), "score": score, "decision": "block",
            })
        return allowed, score, hits, ("" if allowed else "waf:score")


waf_engine = WafEngine()
