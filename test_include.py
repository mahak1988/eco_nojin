import sys
sys.path.insert(0, r'D:\eco_nojin')

# Execute the main module step by step
code = open(r'D:\eco_nojin\services\api_gateway\main.py').read()
# Find the app creation and execute up to that point
parts = code.split('app = FastAPI(title="Eco Nojin API Gateway")')
exec(parts[0] + 'app = FastAPI(title="Eco Nojin API Gateway")')
print('App created')
print('Routes:', len(app.routes))

# Now try including commerce
from services.commerce.routers.commerce import router as commerce_router
print('Commerce router:', commerce_router)
try:
    app.include_router(commerce_router)
    print('Included!')
    print('Routes:', len(app.routes))
    for route in app.routes:
        if hasattr(route, 'path') and 'commerce' in route.path:
            print('Commerce route:', route.path)
except Exception as e:
    print('Error including:', e)
    import traceback
    traceback.print_exc()