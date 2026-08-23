"""
Start FastAPI Server for Testing
==================================
Standalone server for testing Nojin API.

Run: python start_nojin_server.py
"""

import sys
import uvicorn
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(r"D:\eco_nojin")
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 80)
print("🚀 Starting Nojin API Server")
print("=" * 80)

# Create minimal FastAPI app
app = FastAPI(
    title="Nojin Biofertilizer API",
    description="Scientific soil restoration for 2.5 billion people in arid regions",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register Nojin router
try:
    from services.api_gateway.routers import nojin
    app.include_router(nojin.router)
    print("✅ Nojin router registered")
except Exception as e:
    print(f"❌ Error loading router: {e}")
    sys.exit(1)

# Root endpoint
@app.get("/")
def root():
    return {
        "name": "Nojin Biofertilizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/nojin/health",
    }

# Run server
if __name__ == "__main__":
    print("\n📡 Server will start on:")
    print("   http://localhost:8000")
    print("\n📚 Swagger UI:")
    print("   http://localhost:8000/docs")
    print("\n🛑 To stop: Press Ctrl+C")
    print("\n" + "=" * 80)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")