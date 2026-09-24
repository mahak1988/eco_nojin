import sys
import logging
logging.disable(logging.CRITICAL)

for handler in logging.root.handlers[:]:
    handler.setLevel(logging.CRITICAL)

from services.api_gateway.main import app

# Check all routes
all_routes = []
for r in app.router.routes:
    if hasattr(r, 'path'):
        all_routes.append(r.path)

with open('all_routes.txt', 'w') as f:
    for path in sorted(set(all_routes)):
        f.write(f'{path}\n')

print(f'Total routes: {len(all_routes)}')