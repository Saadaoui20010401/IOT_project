import requests
import json

# Test the DHT11 monitoring API
BASE_URL = "http://127.0.0.1:8000"

def test_api_endpoints():
    print("Testing DHT11 Monitoring API Endpoints...")
    
    # Test 1: Send test data to the API
    print("\n1. Testing POST /api/post/ endpoint")
    test_data = {
        "temp": 25.5,
        "hum": 60.2
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/post/", json=test_data)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json() if response.content else 'No content'}")
        print("   ✓ POST request successful")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 2: Get all sensor data
    print("\n2. Testing GET /api/ endpoint")
    try:
        response = requests.get(f"{BASE_URL}/api/")
        print(f"   Status Code: {response.status_code}")
        data = response.json()
        print(f"   Number of records: {len(data) if isinstance(data, list) else 'N/A'}")
        print("   ✓ GET request successful")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 3: Get latest data
    print("\n3. Testing GET /latest/ endpoint")
    try:
        response = requests.get(f"{BASE_URL}/latest/")
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Latest data: {data}")
            print("   ✓ Latest data retrieved successfully")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test 4: Get chart data for day
    print("\n4. Testing GET /api/chart_data/jour/ endpoint")
    try:
        response = requests.get(f"{BASE_URL}/api/chart_data/jour/")
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Chart data points: {len(data.get('labels', []))}")
            print("   ✓ Chart data retrieved successfully")
        else:
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")

if __name__ == "__main__":
    test_api_endpoints()