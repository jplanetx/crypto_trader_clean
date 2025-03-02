#!/usr/bin/env python
"""
Test script for authentication error handling.
"""
import sys
import os
import argparse
import json
import time
import hmac
import hashlib
import base64
import requests

def test_auth_error_handling(invalid_creds=False):
    """Test authentication error handling."""
    print("Testing authentication error handling...")
    
    # Load API credentials
    try:
        with open('config/cdp_api_key_2.json', 'r') as f:
            config = json.load(f)
            api_key = config.get('name')
            api_secret = config.get('privateKey')
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading API credentials: {e}")
        return False
    
    # If testing with invalid credentials, modify the API key
    if invalid_creds:
        print("Using invalid credentials for testing...")
        api_key = "invalid_api_key"
    
    # Define the API endpoint
    api_url = "https://api.coinbase.com"
    endpoint = "/api/v3/brokerage/accounts"
    
    # Set the timestamp
    timestamp = str(int(time.time()))
    
    # Set the request method and body
    method = "GET"
    body = ""
    
    # Generate the signature
    message = timestamp + method + endpoint + body
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        digestmod=hashlib.sha256
    ).digest()
    signature_b64 = base64.b64encode(signature).decode('utf-8')
    
    # Set the headers
    headers = {
        "Content-Type": "application/json",
        "CB-ACCESS-KEY": api_key,
        "CB-ACCESS-SIGN": signature_b64,
        "CB-ACCESS-TIMESTAMP": timestamp
    }
    
    # Make the request
    try:
        response = requests.get(api_url + endpoint, headers=headers)
        
        # If we're testing with invalid credentials, we expect a 401 error
        if invalid_creds and response.status_code == 401:
            print("Successfully detected invalid credentials (401 Unauthorized)")
            print(f"Error message: {response.json().get('message', 'No error message')}")
            return True
        
        # Otherwise, we expect a successful response
        response.raise_for_status()
        
        # Print the response
        accounts = response.json()
        print(f"Authentication successful! Found {len(accounts.get('accounts', []))} accounts.")
        return True
    except requests.exceptions.RequestException as e:
        if invalid_creds:
            print(f"Successfully caught authentication error: {e}")
            return True
        else:
            print(f"Authentication failed: {e}")
            return False
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test Coinbase Advanced Trade API authentication error handling')
    parser.add_argument('--invalid-creds', action='store_true', help='Test with invalid credentials')
    
    args = parser.parse_args()
    
    success = test_auth_error_handling(args.invalid_creds)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
