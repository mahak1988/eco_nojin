#!/usr/bin/env python3
from fastapi.testclient import TestClient

from services.api_gateway.main import app

client = TestClient(app)

# Test legal-texts endpoints
print("Testing legal-texts endpoints...")
r = client.get("/api/v1/legal-texts")
print("GET /api/v1/legal-texts:", r.status_code)
if r.status_code == 200:
    print("  Count:", r.json()["count"])

r = client.get("/api/v1/legal-texts/fa/terms")
print("GET /api/v1/legal-texts/fa/terms:", r.status_code)
if r.status_code == 200:
    print("  Title:", r.json()["title"][:50])

r = client.get("/api/v1/legal-texts/locales")
print("GET /api/v1/legal-texts/locales:", r.status_code)
if r.status_code == 200:
    print("  Locales:", r.json())

# Test tool-registry endpoints
print("\nTesting tool-registry endpoints...")
r = client.get("/api/v1/tool-registry")
print("GET /api/v1/tool-registry:", r.status_code)
if r.status_code == 200:
    print("  Count:", r.json()["count"])

r = client.get("/api/v1/tool-registry/domains")
print("GET /api/v1/tool-registry/domains:", r.status_code)
if r.status_code == 200:
    print("  Domains:", r.json())

r = client.get("/api/v1/tool-registry/H01")
print("GET /api/v1/tool-registry/H01:", r.status_code)
if r.status_code == 200:
    print("  Tool:", r.json()["name_en"])

r = client.get("/api/v1/tool-registry/by-service/models/et0_hargreaves")
print("GET /api/v1/tool-registry/by-service/models/et0_hargreaves:", r.status_code)
if r.status_code == 200:
    print("  Tool:", r.json()["name_en"])
