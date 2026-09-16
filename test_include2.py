import sys
sys.path.insert(0, r'D:\eco_nojin')

# Execute main.py step by step to see where it fails
import importlib.util
spec = importlib.util.spec_from_file_location('main', r'D:\eco_nojin\services\api_gateway\main.py')
main_module = importlib.util.module_from_spec(spec)

# Execute up to app creation
code = open(r'D:\eco_nojin\services\api_gateway\main.py').read()
parts = code.split('app = FastAPI(title="Eco Nojin API Gateway")')
exec(parts[0] + 'app = FastAPI(title="Eco Nojin API Gateway")', main_module.__dict__)
print('App created')

# Now check if commerce_router is in the namespace
print('commerce_router in namespace:', 'commerce_router' in main_module.__dict__)
if 'commerce_router' in main_module.__dict__:
    print('commerce_router:', main_module.__dict__['commerce_router'])
    
    # Try including it
    main_module.__dict__['app'].include_router(main_module.__dict__['commerce_router'])
    print('Included!')
    print('Routes:', len(main_module.__dict__['app'].router.routes))
    for route in main_module.__dict__['app'].router.routes:
        if hasattr(route, 'path') and 'commerce' in route.path:
            print('Commerce route:', route.path, route.methods)