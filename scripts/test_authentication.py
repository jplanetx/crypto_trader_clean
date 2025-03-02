#!/usr/bin/env python
"""
Test script for authentication functionality.
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

def test_authentication(api_key=None, api_secret=None, dry_run=False):
    """Test the authentication with Coinbase Advanced Trade API."""
    print("Testing authentication with Coinbase Advanced Trade API...")
    
    if dry_run:
        print("Dry run mode - skipping actual API calls")
        return True
    
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
    parser = argparse.ArgumentParser(description='Test Coinbase Advanced Trade API authentication')
    parser.add_argument('--api-key', help='API key')
    parser.add_argument('--api-secret', help='API secret')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    
    args = parser.parse_args()
    
    success = test_authentication(args.api_key, args.api_secret, args.dry_run)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
