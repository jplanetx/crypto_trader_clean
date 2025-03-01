import time
import hmac
import hashlib
import base64
import requests
import json
from urllib.parse import urlencode

def setup_coinbase_auth():
    """
    Set up and test the Coinbase API authentication.
    Returns the authenticated client if successful.
    """
    # Load API credentials from file
    try:
        with open("config/cdp_api_key_2.json", "r") as f:
            credentials = json.load(f)
        api_key = credentials["name"]
        api_secret = credentials["privateKey"]
    except FileNotFoundError:
        print("Error: config/cdp_api_key_2.json not found.")
        return None
    except KeyError as e:
        print(f"Error: Missing key in config file: {e}")
        return None
    except json.JSONDecodeError:
        print("Error: Invalid JSON in config/cdp_api_key_2.json")
        return None

    # Test the authentication
    timestamp = str(int(time.time()))
    request_path = '/accounts'
    method = 'GET'
    
    # Create the message to sign
    message = timestamp + method + request_path
    
    # Create the signature using HMAC
    hmac_key = api_secret.encode('utf-8')
    signature = hmac.new(hmac_key, message.encode('utf-8'), hashlib.sha256)
    signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')
    
    # Set up the headers
    headers = {
        'CB-ACCESS-KEY': api_key,
        'CB-ACCESS-SIGN': signature_b64,
        'CB-ACCESS-TIMESTAMP': timestamp,
        'Content-Type': 'application/json'
    }
    
    # Make a test request
    api_url = "https://api.exchange.coinbase.com"
    response = requests.get(f"{api_url}{request_path}", headers=headers)
    
    if response.status_code == 200:
        print("Authentication successful!")
        # Create and return the client
        from coinbase.rest import RESTClient
        client = RESTClient(api_key=api_key, api_secret=api_secret, api_passphrase=api_passphrase)
        return client
    else:
        print(f"Authentication failed! Status code: {response.status_code}")
        print(f"Response: {response.text}")
        print("\nPossible issues:")
        print("1. API key or secret is incorrect")
        print("2. API key doesn't have necessary permissions")
        print("3. System time is not synchronized")
        print("4. API passphrase is incorrect (if required)")
        print("5. Request rate limit exceeded")
        return None

if __name__ == '__main__':
    setup_coinbase_auth()
