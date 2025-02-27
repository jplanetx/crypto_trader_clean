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
api_key_parts = api_key.split('/')
if len(api_key_parts) >= 4:
    api_key_id = api_key_parts[-1]  # Get the last part which should be the key ID
else:
    api_key_id = api_key  # Use as is if not in the expected format

print(f"Using API Key ID: {api_key_id}")
print(f"Private Key (first 20 chars): {private_key[:20]}...")

# Define the API endpoint
base_url = "https://api.coinbase.com"
endpoint = "/api/v3/brokerage/accounts"
auth_endpoint = "/users/self/verify"

# Set the request path
request_path = endpoint

# Set the timestamp (in seconds)
timestamp = str(int(time.time()))
method = "GET"
request_path = endpoint
body = ""

# Create the prehash string by concatenating timestamp, HTTP method, and auth_endpoint
prehash_string = timestamp + method + auth_endpoint + body
print(f"Prehash string: {prehash_string}")

request_path = endpoint

# Create the signature by signing the prehash with the private key using HMAC-SHA256
try:
    # Try using the private key directly
    signature = hmac.new(
        private_key.encode('utf-8'),
        prehash_string.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    
    # Base64 encode the signature
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    print(f"Signature: {signature_b64}")
    
    # Set the headers according to the documentation
    headers = {
        "CB-ACCESS-KEY": api_key_id,  # API key
        "CB-ACCESS-SIGN": signature_b64,  # Base64-encoded signature
        "CB-ACCESS-TIMESTAMP": timestamp,  # Timestamp for the request
        "Content-Type": "application/json"  # Content type
    }
    
    print(f"Request Headers: {headers}")
    print(f"Making request to: {base_url}{endpoint}")
    
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
    
except Exception as e:
    print(f"Error: {e}")
    if isinstance(e, requests.exceptions.RequestException) and hasattr(e, 'response') and e.response:
        print(f"Response status code: {e.response.status_code}")
        print(f"Response body: {e.response.text}")

# If the above fails, try an alternative approach
if 'response' not in locals() or response.status_code != 200:
    print("\nTrying alternative approach...")
    
    # Try using just the key part of the private key (remove PEM headers)
    try:
        # Remove PEM headers and extract just the key part
        key_parts = private_key.split('-----')
        if len(key_parts) >= 3:
            key_content = key_parts[2].replace('BEGIN EC PRIVATE KEY', '').replace('END EC PRIVATE KEY', '').strip()
            print(f"Extracted key content (first 20 chars): {key_content[:20]}...")
            
            # Create signature with just the key content
            signature = hmac.new(
                key_content.encode('utf-8'),
                prehash_string.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            
            # Base64 encode the signature
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            print(f"Alternative Signature: {signature_b64}")
            
            # Set the headers
            headers = {
                "CB-ACCESS-KEY": api_key_id,
                "CB-ACCESS-SIGN": signature_b64,
                "CB-ACCESS-TIMESTAMP": timestamp,
                "Content-Type": "application/json"
            }
            
            print(f"Alternative Request Headers: {headers}")
            print(f"Making alternative request to: {base_url}{endpoint}")
            
            # Make the request
            response = requests.get(base_url + endpoint, headers=headers)
            
            # Print response status
            print(f"Alternative Response Status Code: {response.status_code}")
            
            # Try to parse response as JSON
            try:
                response_json = response.json()
                print(f"Alternative Response: {json.dumps(response_json, indent=2)}")
            except:
                print(f"Alternative Raw Response: {response.text}")
            
            # Raise exception for non-2xx status codes
            response.raise_for_status()
            
        else:
            print("Could not extract key content from private key")
            
    except Exception as e:
        print(f"Alternative approach error: {e}")
        if isinstance(e, requests.exceptions.RequestException) and hasattr(e, 'response') and e.response:
            print(f"Alternative response status code: {e.response.status_code}")
            print(f"Alternative response body: {e.response.text}")