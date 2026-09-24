import sys
import logging
logging.disable(logging.CRITICAL)

for handler in logging.root.handlers[:]:
    handler.setLevel(logging.CRITICAL)

from services.api_gateway.main import app

admin_routes = []
for r in app.router.routes:
    if hasattr(r, 'path') and '/api/v1/admin' in r.path:
        methods = r.methods if hasattr(r, 'methods') else 'N/A'
        admin_routes.append((r.path, methods))

with open('admin_routes.txt', 'w') as f:
    for path, methods in sorted(admin_routes):
        f.write(f'{path} - {methods}\n')

print(f'Found {len(admin_routes)} admin routes')