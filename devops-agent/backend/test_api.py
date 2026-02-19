#!/usr/bin/env python3
"""Test script to debug API issues"""

import requests
import json
import sys

BACKEND_URL = "http://localhost:5000"

def test_api():
    print("=" * 60)
    print("Testing DevOps Agent API")
    print("=" * 60)
    
    # Test 1: Health check
    print("\n1. Testing /api/health...")
    try:
        response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ ERROR: Cannot connect to backend!")
        print("   Make sure backend is running: python app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Analyze endpoint with a simple repo
    print("\n2. Testing /api/analyze with test repository...")
    test_repo = "https://github.com/aashish1019/P11.git"
    print(f"   Repository: {test_repo}")
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/analyze",
            json={"repo_url": test_repo},
            timeout=60
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Analysis completed!")
            print(f"   Job ID: {data.get('job_id', 'N/A')}")
            if 'results' in data:
                results = data['results']
                print(f"   Repository: {results.get('repository', 'N/A')}")
                print(f"   Status: {results.get('final_status', 'N/A')}")
                print(f"   Failures: {results.get('total_failures', 0)}")
                print(f"   Fixes: {results.get('total_fixes', 0)}")
        else:
            print(f"   ❌ Analysis failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
                if 'details' in error_data:
                    print(f"   Details: {error_data['details'][:500]}")  # First 500 chars
            except:
                print(f"   Response: {response.text[:500]}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ⚠️  Request timed out (this is normal for large repos)")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("API test complete!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    try:
        import requests
    except ImportError:
        print("Installing requests library...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"])
        import requests
    
    success = test_api()
    sys.exit(0 if success else 1)
