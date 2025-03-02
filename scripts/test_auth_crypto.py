#!/usr/bin/env python
"""
Test script for authentication with token refresh functionality.
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

def test_auth_with_refresh(api_key=None, api_secret=None, force_refresh=False):
    """Test the authentication with token refresh."""
    print("Testing authentication with token refresh...")
    
    # Load API credentials if not provided
    if not api_key or not api_secret:
        try:
            with open('config/cdp_api_key_2.json', 'r') as f:
                config = json.load(f)
                api_key = config.get('name')
                api_secret = config.get('privateKey')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading API credentials: {e}")
            return False
    
    if not api_key or not api_secret:
        print("API key and secret are required")
        return False
    
    # Define the API endpoint
    api_url = "https://api.coinbase.com"
    endpoint = "/api/v3/brokerage/accounts"
    
    # Simulate token expiration if force_refresh is True
    if force_refresh:
        print("Simulating token expiration...")
        # Use an expired timestamp to force a 401 response
        timestamp = str(int(time.time()) - 3600)  # 1 hour ago
    else:
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
        
        # If we get a 401 (unauthorized) and force_refresh is True, retry with a new token
        if response.status_code == 401 and force_refresh:
            print("Received 401 unauthorized, refreshing token...")
            
            # Generate a new timestamp and signature
            timestamp = str(int(time.time()))
            message = timestamp + method + endpoint + body
            signature = hmac.new(
                api_secret.encode('utf-8'),
                message.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            signature_b64 = base64.b64encode(signature).decode('utf-8')
            
            # Update the headers with the new timestamp and signature
            headers["CB-ACCESS-TIMESTAMP"] = timestamp
            headers["CB-ACCESS-SIGN"] = signature_b64
            
            # Retry the request
            print("Retrying with refreshed token...")
            response = requests.get(api_url + endpoint, headers=headers)
        
        response.raise_for_status()
        
        # Print the response
        accounts = response.json()
        print(f"Authentication successful! Found {len(accounts.get('accounts', []))} accounts.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Authentication failed: {e}")
        return False
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Test Coinbase Advanced Trade API authentication with token refresh')
    parser.add_argument('--api-key', help='API key')
    parser.add_argument('--api-secret', help='API secret')
    parser.add_argument('--force-refresh', action='store_true', help='Force token refresh')
    
    args = parser.parse_args()
    
    success = test_auth_with_refresh(args.api_key, args.api_secret, args.force_refresh)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
