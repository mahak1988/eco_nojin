#!/usr/bin/env python3
"""Generate OpenAPI schema for contract testing."""

import json
import sys

sys.path.insert(0, ".")

from fastapi.openapi.utils import get_openapi

from services.api_gateway.main import app

schema = get_openapi(title=app.title, version="0.1.0", routes=app.routes)
with open("openapi_schema.json", "w") as f:
    json.dump(schema, f, indent=2)

print("Full OpenAPI schema generated")
print(f"Paths: {len(schema.get('paths', {}))}")
