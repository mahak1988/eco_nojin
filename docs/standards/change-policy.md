# Integration change policy

The plan's risk table lists two operational risks that are about how the work
is sequenced rather than about code:

* **the feature freeze halts delivery** — mitigated by "an explicit exception
  for critical fixes";
* **queues contract before the workers are ready** — mitigated by "attach the
  adapter removal to the same PR as the last consumer's migration".

Both are decisions, not tests, so they are recorded here with the condition
that makes each one safe. This file is referenced by
`tests/contract/test_change_policy.py`.

## The feature freeze: what is frozen, and the exception

**Frozen since 2026-09-28** (start of phase 4): no new capability in
`services/`. The freeze covers features, not:

- security fixes,
- data-loss defects,
- a change that unblocks a frozen item (a missing test, a broken import, an
  absent schema),
- anything that removes debt recorded in the toleration ledger.

**The exception is explicit and recorded**, not implicit in a commit message.
An exception needs three things, in the PR description:

1. which condition above it claims,
2. what the customer-visible harm of *not* doing it would be,
3. what was considered and rejected.

An exception that cannot state (2) is not an exception; it is a preference,
and preferences wait for the freeze to lift.

## Queue contraction: the rule

**Do not remove an adapter, a compat shim, or a deprecated signature in its own
change.** Leave it until the last consumer has moved, then remove it in the
same PR that moves that last consumer.

The failure this prevents: a shim removed while a consumer still routes
through it, and the resulting error surfacing on a path with no test.

In practice, in this campaign, the deprecations that mattered were:

| Shim | Removed when |
|---|---|
| `security/headers.py` CSP-only middleware | never mounted; removed with an explicit decision, not as a dependency cleanup |
| `redis_rate_limit.py` | never imported; removed with the rest of `services/security/` dead code |
| `session_manager.py`, `two_factor.py` | never imported; recorded in the deletion log |
| `EcowalletService` fixture | the class never existed; the fixture was removed, not repaired |
| `payout_service.process_payout` (serial vs async) | the async one is now the only caller |

If a shim has no callers, it is not a queue — it is dead code, and the deletion
log is the right place for it. The rule above is for shims that still have
callers.

## The one thing not to do

Do not batch "while I am in here" removals into a change whose subject is
something else. Every deletion in this campaign is individually attributed in
`docs/metrics/deletions.json`; a deletion smuggled into a feature PR has no
such record, and that is how the deletion log became worth having.
