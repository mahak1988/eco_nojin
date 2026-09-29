"""`services.content` package marker.

Missing marker meant this directory resolved as a PEP 420 namespace package,
so pytest could not import a test module beneath it:
``ModuleNotFoundError: No module named 'services.<pkg>.<sub>.<module>'``, and
``services/map_engine/tests/test_integration.py`` failed collection on every full run.
"""

