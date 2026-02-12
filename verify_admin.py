import requests
import sys

BASE_URL = "http://localhost:8001"
API_V1 = f"{BASE_URL}/api/v1"

def test_health():
    print("Testing /health...")
    try:
        r = requests.get(f"{BASE_URL}/health")
        if r.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {r.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)

def test_admin_unauthorized():
    print("\nTesting /admin/system-context (Unauthorized)...")
    r = requests.get(f"{API_V1}/admin/system-context")
    if r.status_code == 401:
        print("✅ Correctly rejected (401 Unauthorized)")
    else:
        print(f"❌ Unexpected status code: {r.status_code} (Expected 401)")

def test_admin_flow():
    print("\nTesting Admin Login & Access...")
    # Credentials from previous conversation history
    payload = {
        "username": "admin@forsee.ai",
        "password": "password123"
    }
    
    # Login
    r = requests.post(f"{API_V1}/auth/login/access-token", data=payload)
    if r.status_code != 200:
        print(f"⚠️ Login failed: {r.status_code} {r.text}")
        print("Skipping authenticated tests.")
        return

    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")

    # Test System Context
    print("Testing /admin/system-context (Authorized)...")
    r = requests.get(f"{API_V1}/admin/system-context", headers=headers)
    if r.status_code == 200:
        print("✅ System Context retrieved:", r.json())
    else:
        print(f"❌ Failed to retrieve System Context: {r.status_code} {r.text}")

    # Test KPIs
    print("Testing /admin/kpi (Authorized)...")
    r = requests.get(f"{API_V1}/admin/kpi", headers=headers)
    if r.status_code == 200:
        print("✅ KPIs retrieved:", r.json())
    else:
        print(f"❌ Failed to retrieve KPIs: {r.status_code} {r.text}")

if __name__ == "__main__":
    test_health()
    test_admin_unauthorized()
    test_admin_flow()
