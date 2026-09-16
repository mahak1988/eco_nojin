import sys
sys.path.insert(0, r'D:\eco_nojin')
import importlib
import services.api_gateway.main as main_module
importlib.reload(main_module)

app = main_module.app

# Add debug to see what routes are added
original_include = app.router.include_router

def debug_include(router, **kwargs):
    print('Including router:', router, 'prefix:', kwargs.get('prefix', ''))
    print('Router routes:', len(router.routes))
    for r in router.routes:
        if hasattr(r, 'path'):
            print('  Route:', r.path, r.methods)
    result = original_include(router, **kwargs)
    print('After include, total routes:', len(app.router.routes))
    return result

app.router.include_router = debug_include

# Now include commerce
app.include_router(main_module.commerce_router)

print('Final routes:', len(app.router.routes))