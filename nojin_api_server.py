"""
Standalone Nojin API Server
=============================
Independent FastAPI server specifically for Nojin Biofertilizer API.
No dependencies on main app structure.

Run: python nojin_api_server.py
Then access: http://localhost:8001/docs
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(r"D:\eco_nojin")
sys.path.insert(0, str(PROJECT_ROOT))

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print("=" * 80)
print("🚀 Starting Standalone Nojin API Server")
print("=" * 80)

# Create dedicated FastAPI app
app = FastAPI(
    title="Nojin Biofertilizer API",
    description="""
## Scientific Soil Restoration for 2.5 Billion People in Arid Regions

### Features
- 43 scientifically-documented materials
- 10 soil types with restoration recipes
- 4 advanced calculators (LP, Cost-Benefit, Water, Scale)
- Persistence-based reinvestment logic
- Economically validated: 44.8% ROI, 26-month payback

### Key Endpoints
- `/api/nojin/health` - Health check
- `/api/nojin/materials` - List materials
- `/api/nojin/full-analysis` - Complete analysis ⭐
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", tags=["Root"])
def root():
    return {
        "name": "Nojin Biofertilizer API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/api/nojin/health",
        "materials": "/api/nojin/materials",
        "full_analysis": "/api/nojin/full-analysis",
    }

# Import and register Nojin router
print("\n📋 Loading Nojin router...")
try:
    # Try multiple possible locations
    router_loaded = False
    
    # Location 1: services/api_gateway/routers/nojin.py
    try:
        from services.api_gateway.routers import nojin
        app.include_router(nojin.router)
        print("✅ Loaded from: services.api_gateway.routers.nojin")
        router_loaded = True
    except ImportError:
        pass
    
    # Location 2: Direct import from file
    if not router_loaded:
        router_file = PROJECT_ROOT / "services" / "api_gateway" / "routers" / "nojin.py"
        if router_file.exists():
            import importlib.util
            spec = importlib.util.spec_from_file_location("nojin_router", router_file)
            nojin_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(nojin_module)
            app.include_router(nojin_module.router)
            print("✅ Loaded directly from file")
            router_loaded = True
    
    if not router_loaded:
        print("❌ Could not load Nojin router")
        print("   Expected locations:")
        print("   • services.api_gateway.routers.nojin")
        print(f"   • {router_file.relative_to(PROJECT_ROOT)}")
        sys.exit(1)
    
    # List registered routes
    print("\n📋 Registered routes:")
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            methods = ",".join(route.methods) if route.methods else "ANY"
            print(f"   {methods:6s} {route.path}")
    
except Exception as e:
    print(f"❌ Error loading router: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("✅ NOJIN API SERVER READY")
print("=" * 80)
print(f"""
🌐 Access points:
   • API Base:     http://localhost:8001
   • Swagger UI:   http://localhost:8001/docs
   • ReDoc:        http://localhost:8001/redoc
   • OpenAPI JSON: http://localhost:8001/openapi.json

🧪 Quick tests (in another terminal):
   curl http://localhost:8001/api/nojin/health
   curl http://localhost:8001/api/nojin/materials
   curl http://localhost:8001/api/nojin/statistics

🛑 To stop: Press Ctrl+C

📊 Example POST request:
   curl -X POST http://localhost:8001/api/nojin/full-analysis \\
     -H "Content-Type: application/json" \\
     -d '{{
       "soil_code": "SOIL-01",
       "area_ha": 10.0,
       "crop_type": "wheat"
     }}'
""")

# Run the server on port 8001 to avoid conflict with main app
if __name__ == "__main__":
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info",
    )