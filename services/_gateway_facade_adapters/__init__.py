"""Per-domain engine adapters for the gateway facade (A-2 step 1).

Each module holds one domain's direct ``engine.*`` imports plus the thin
wrappers that expose them under the facade's existing public names. The facade
(:mod:`services._gateway_facade`) imports these names and re-exports them, so
its public surface is unchanged while the six engine-import sites that made it
a God-object move behind a domain boundary.

This package is the continuation of the same sanctioned bridge
``services/_gateway_facade.py`` has always been: every ``engine.*`` import
below used to sit directly in the facade, and every one is listed in
``tools/import_guard_policy.json`` under
``SERVICES_NO_ENGINE_INTERNALS.facade_files``.
"""
