"""
Restart server and run tests
==============================
Convenience script to stop, restart, and test.

Run: python restart_and_test.py
"""

import subprocess
import time
import sys
import signal
import os
from pathlib import Path

PROJECT_ROOT = Path(r"D:\eco_nojin")

print("=" * 80)
print("🔄 RESTARTING SERVER AND TESTING")
print("=" * 80)

# Step 1: Kill any existing uvicorn processes
print("\n📋 Step 1: Killing existing uvicorn processes...")
try:
    result = subprocess.run(
        ["taskkill", "/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq uvicorn*"],
        capture_output=True,
        timeout=5,
    )
    # Also try to find and kill uvicorn specifically
    result2 = subprocess.run(
        ["Get-Process", "python", "-ErrorAction", "SilentlyContinue"],
        shell=True,
        capture_output=True,
        timeout=5,
    )
except Exception as e:
    print(f"   ℹ️  Could not auto-kill: {e}")

print("   ✅ Killed (if any)")
time.sleep(2)

# Step 2: Start server in background
print("\n📋 Step 2: Starting server on port 8000...")
print("   ⏳ Waiting 10 seconds for startup...")

# Use subprocess.Popen for non-blocking
env = os.environ.copy()
server_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", 
     "services.api_gateway.main:app",
     "--host", "127.0.0.1",
     "--port", "8000"],
    cwd=PROJECT_ROOT,
    env=env,
)

# Wait for startup
time.sleep(10)

# Step 3: Run tests
print("\n📋 Step 3: Running tests...")
result = subprocess.run(
    [sys.executable, "test_nojin_unified.py"],
    cwd=PROJECT_ROOT,
    env=env,
)

if result.returncode == 0:
    print("\n🎉 All tests passed!")
else:
    print("\n⚠️  Some tests failed")

print("\n📡 Server is still running on port 8000")
print("   Press Ctrl+C to stop")

try:
    server_proc.wait()
except KeyboardInterrupt:
    print("\n🛑 Stopping server...")
    server_proc.terminate()
    try:
        server_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_proc.kill()
    print("✅ Server stopped")