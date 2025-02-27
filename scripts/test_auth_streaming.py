import json
import requests
import hmac
import hashlib
import time
import base64
from base64 import b64encode

# Load API keys from file
with open('config/cdp_api_key_2.json', 'r') as f:
    api_keys = json.load(f)

api_key = api_keys['name']
private_key = api_keys['privateKey']

# Extract the actual API key ID from the full string
api_key_id = api_key.split('/')[-1]

print(f"Using API Key ID: {api_key_id}")
print(f"Private Key (first 20 chars): {private_key[:20]}...")

# Define the API endpoint
base_url = "https://api.coinbase.com"
endpoint = "/api/v3/brokerage/accounts"  # List accounts endpoint

# Set the timestamp (in seconds)
timestamp = str(int(time.time()))

# This is how coinbase_streaming.py creates the message and signature
# See lines 94-100 in src/core/coinbase_streaming.py
message = timestamp + 'GET' + '/api/v3/brokerage/accounts'
signature = hmac.new(
    private_key.encode('utf-8'),
    message.encode('utf-8'),
    digestmod=hashlib.sha256
).digest()
signature_b64 = b64encode(signature).decode('utf-8')

print(f"Message to sign (from streaming): {message}")
print(f"Signature (from streaming): {signature_b64}")

# Set the headers according to the streaming implementation
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

# Try with the correct endpoint path in the message
print("\nTrying with correct endpoint path in message...")

# Create the message with the actual endpoint path
message = timestamp + 'GET' + endpoint
signature = hmac.new(
    private_key.encode('utf-8'),
    message.encode('utf-8'),
    digestmod=hashlib.sha256
).digest()
signature_b64 = b64encode(signature).decode('utf-8')

print(f"Message to sign (with correct path): {message}")
print(f"Signature (with correct path): {signature_b64}")

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