import sys
import logging
logging.disable(logging.CRITICAL)

for handler in logging.root.handlers[:]:
    handler.setLevel(logging.CRITICAL)

# Import routers explicitly to trigger route registration
from services.api_gateway.routers import admin_users, admin_content, admin_bots, admin_errors, admin_settings, admin_models, admin_overview, admin_security

# Check each router's routes
for name, router in [
    ('admin_users', admin_users.router),
    ('admin_content', admin_content.router),
    ('admin_bots', admin_bots.router),
    ('admin_errors', admin_errors.router),
    ('admin_settings', admin_settings.router),
    ('admin_models', admin_models.router),
    ('admin_overview', admin_overview.router),
    ('admin_security', admin_security.router),
]:
    print(f'{name}: {len(router.routes)} routes')
    for r in router.routes:
        if hasattr(r, 'path'):
            print(f'  {r.path} - {r.methods}')