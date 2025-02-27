import json
import requests
import hmac
import hashlib
import time
import base64
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

# Load API keys from file
with open('config/cdp_api_key_2.json', 'r') as f:
    api_keys = json.load(f)

api_key = api_keys['name']
private_key_pem = api_keys['privateKey']

print(f"API Key: {api_key}")
print(f"Private Key: {private_key_pem}")

# Use the full API key as the CB-ACCESS-KEY value
api_key_id = api_key
print(f"Using full API Key: {api_key_id}")

# Parse the private key
try:
    # Remove header and footer and decode
    private_key_lines = private_key_pem.strip().split('-----')
    if len(private_key_lines) >= 3:
        private_key_base64 = private_key_lines[2].replace('BEGIN EC PRIVATE KEY', '').replace('END EC PRIVATE KEY', '').strip()
        private_key_bytes = base64.b64decode(private_key_base64)
        print("Successfully parsed private key")
    else:
        # Try to load the PEM directly
        private_key = serialization.load_pem_private_key(
            private_key_pem.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        print("Successfully loaded private key using cryptography")
        private_key_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
except Exception as e:
    print(f"Error parsing private key: {e}")
    private_key_bytes = private_key_pem.encode('utf-8')  # Fallback to using the PEM as is

# Define the API endpoint
api_url = "https://api.exchange.coinbase.com"
endpoint = "/api/v3/brokerage/accounts"

# Function to generate the signature
def generate_signature(timestamp, method, request_path, body, private_key_bytes):
    message = str(timestamp) + method + request_path + body
    signature = hmac.new(
        private_key_bytes,
        message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    return signature_b64

try:
    # Set the timestamp
    timestamp = str(int(time.time()))

    # Set the request method and body
    method = "GET"
    body = ""

    # Generate the signature
    signature = generate_signature(timestamp, method, endpoint, body, private_key_bytes)

    # Set the headers
    headers = {
        "Content-Type": "application/json",
        "CB-ACCESS-KEY": api_key_id,  # Use the extracted key ID
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp
    }

    print(f"Request Headers: {headers}")

    # Make the request
    response = requests.get(api_url + endpoint, headers=headers)
    response.raise_for_status()

    # Print the response
    print("Accounts:", response.json())

except requests.exceptions.RequestException as e:
    print(f"Authentication failed: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response status code: {e.response.status_code}")
        print(f"Response body: {e.response.text}")
except Exception as e:
    print(f"Authentication failed: {e}")
