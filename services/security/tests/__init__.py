"""Test package marker for `services/security/tests`.

Required so pytest imports this directory as a distinct package. Fourteen directories
contain a module named ``test_integration.py``; without this marker pytest
resolves them all to the top-level name ``tests.test_integration`` and collection
fails with ``ModuleNotFoundError: No module named 'tests.test_integration'``.
"""

