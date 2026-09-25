#!/usr/bin/env python3
"""Generate OpenAPI schema for contract testing."""

import json
import sys
from pathlib import Path

sys.path.insert(0, ".")

from fastapi.openapi.utils import get_openapi

from services.api_gateway.main import app

schema = get_openapi(title=app.title, version="0.1.0", routes=app.routes)
with Path("openapi.json").open("w", encoding="utf-8") as f:
    json.dump(schema, f, indent=2)

print("Full OpenAPI schema generated")
print(f"Paths: {len(schema.get('paths', {}))}")
