import json
import requests
import hmac
import hashlib
import time
import base64
import os

# Load API keys from file
with open('config/cdp_api_key_2.json', 'r') as f:
    api_keys = json.load(f)

api_key = api_keys['name']
private_key = api_keys['privateKey']

# Extract the actual API key ID from the full string
# Format: organizations/org_id/apiKeys/key_id
api_key_parts = api_key.split('/')
if len(api_key_parts) >= 4:
    api_key_id = api_key_parts[-1]  # Get the last part which should be the key ID
else:
    api_key_id = api_key  # Use as is if not in the expected format

print(f"Using API Key ID: {api_key_id}")
print(f"Private Key (first 20 chars): {private_key[:20]}...")

# Define the API endpoint
base_url = "https://api.coinbase.com"
endpoint = "/api/v3/brokerage/products"  # List products endpoint

# Set the timestamp
timestamp = str(int(time.time()))
method = "GET"
request_path = endpoint
body = ""

# Create the message to sign
message = timestamp + method + request_path + body
print(f"Message to sign: {message}")

# Sign the message
signature = hmac.new(
    private_key.encode('utf-8'),
    message.encode('utf-8'),
    digestmod=hashlib.sha256
).digest()

signature_b64 = base64.b64encode(signature).decode('utf-8')
print(f"Signature: {signature_b64}")

# Set the headers
headers = {
    "Content-Type": "application/json",
    "CB-ACCESS-KEY": api_key_id,
    "CB-ACCESS-SIGN": signature_b64,
    "CB-ACCESS-TIMESTAMP": timestamp
}

print(f"Request Headers: {headers}")
print(f"Making request to: {base_url}{endpoint}")

try:
    # Make the request
    response = requests.get(base_url + endpoint, headers=headers)
    
    # Print response status
    print(f"Response Status Code: {response.status_code}")
    
    # Try to parse response as JSON
    try:
        response_json = response.json()
        print(f"Response: {json.dumps(response_json, indent=2)}")
    except:
        print(f"Raw Response: {response.text}")
    
    # Raise exception for non-2xx status codes
    response.raise_for_status()
    
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response status code: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
except Exception as e:
    print(f"Error: {e}")