import requests
import json

# Define the API endpoint
base_url = "https://api.coinbase.com"
endpoint = "/api/v3/brokerage/products"  # Try as a public endpoint

print(f"Making request to: {base_url}{endpoint}")

try:
    # Make the request without authentication headers
    response = requests.get(base_url + endpoint)
    
    # Print response status
    print(f"Response Status Code: {response.status_code}")
    
    # Try to parse response as JSON
    try:
        response_json = response.json()
        print(f"Response: {json.dumps(response_json, indent=2)}")
    except:
        print(f"Raw Response: {response.text}")
    
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response status code: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
except Exception as e:
    print(f"Error: {e}")

# Try another potential public endpoint
print("\nTrying another endpoint...")
endpoint2 = "/api/v3/brokerage/products/BTC-USD/ticker"

print(f"Making request to: {base_url}{endpoint2}")

try:
    # Make the request without authentication headers
    response = requests.get(base_url + endpoint2)
    
    # Print response status
    print(f"Response Status Code: {response.status_code}")
    
    # Try to parse response as JSON
    try:
        response_json = response.json()
        print(f"Response: {json.dumps(response_json, indent=2)}")
    except:
        print(f"Raw Response: {response.text}")
    
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response status code: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
except Exception as e:
    print(f"Error: {e}")