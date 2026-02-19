#!/usr/bin/env python3
"""Quick test script to verify backend is working"""

import requests
import json

BACKEND_URL = "http://localhost:5000"

def test_backend():
    print("Testing DevOps Agent Backend...")
    print(f"Backend URL: {BACKEND_URL}\n")
    
    # Test 1: Health check
    print("1. Testing /api/health endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        print("   ✅ Health check passed\n")
    except requests.exceptions.ConnectionError:
        print("   ❌ ERROR: Cannot connect to backend!")
        print("   Make sure backend is running: python app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        return False
    
    # Test 2: Root endpoint
    print("2. Testing root endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2)}")
        print("   ✅ Root endpoint works\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    # Test 3: Analyze endpoint (without actually analyzing)
    print("3. Testing /api/analyze endpoint structure...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/analyze",
            json={"repo_url": ""},
            timeout=5
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 400:
            print("   ✅ Endpoint is working (expected 400 for empty URL)\n")
        else:
            print(f"   ⚠️  Unexpected status code\n")
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
    
    print("Backend test complete!")
    return True

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("Installing requests library...")
        import subprocess
        subprocess.run(["pip", "install", "requests"])
        import requests
    
    test_backend()
