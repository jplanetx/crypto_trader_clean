import json
import requests
import hashlib
import hmac
import time
import base64

# Load API keys from file
with open('config/cdp_api_key_2.json', 'r') as f:
    api_keys = json.load(f)

api_key = api_keys['name']
private_key = api_keys['privateKey']

print(f"API Key: {api_key}")
print(f"Private Key: {private_key}")

# Define the API endpoint
api_url = "https://api.coinbase.com"
endpoint = "/api/v3/brokerage/accounts"

# Function to generate the signature
def generate_signature(timestamp, method, request_path, body, private_key):
    message = str(timestamp) + method + request_path + body
    signature = hmac.new(
        private_key.encode('utf-8'),
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
    signature = generate_signature(timestamp, method, endpoint, body, private_key)

    # Set the headers
    headers = {
        "Content-Type": "application/json",
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-SIGN": signature,
        "CB-ACCESS-TIMESTAMP": timestamp
    }

    # Make the request
    response = requests.get(api_url + endpoint, headers=headers)
    response.raise_for_status()

    # Print the response
    print("Accounts:", response.json())

except requests.exceptions.RequestException as e:
    print(f"Authentication failed: {e}")
except Exception as e:
    print(f"Authentication failed: {e}")
