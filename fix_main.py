with open(r'D:\eco_nojin\services\api_gateway\main.py', 'r') as f:
    content = f.read()

# Add manual route inclusion after commerce_router include
old = 'app.include_router(commerce_router)'
new = '''app.include_router(commerce_router)
# Workaround: FastAPI include_router not resolving routes for commerce router
# Manually add commerce routes to ensure they are registered
from fastapi.routing import APIRoute
for _route in commerce_router.routes:
    if hasattr(_route, "path") and _route.path not in [r.path for r in app.router.routes if hasattr(r, "path")]:
        app.router.routes.append(_route)'''

content = content.replace(old, new)

with open(r'D:\eco_nojin\services\api_gateway\main.py', 'w') as f:
    f.write(content)
print('Fixed main.py')