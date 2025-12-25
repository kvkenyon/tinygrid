#!/usr/bin/env python3
"""Debug script to test ERCOT authentication endpoint"""

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import httpx
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent
load_dotenv(env_path / ".env")

username = os.getenv("ERCOT_USERNAME")
password = os.getenv("ERCOT_PASSWORD")
subscription_key = os.getenv("ERCOT_SUBSCRIPTION_KEY")

if not all([username, password, subscription_key]):
    print("Error: Missing required environment variables")
    print("Please set ERCOT_USERNAME, ERCOT_PASSWORD, and ERCOT_SUBSCRIPTION_KEY")
    sys.exit(1)

# ERCOT Azure B2C endpoint
endpoint = "https://ercotb2c.b2clogin.com/ercotb2c.onmicrosoft.com/B2C_1_PUBAPI-ROPC-FLOW/oauth2/v2.0/token"
client_id = "fec253ea-0d06-4272-a5e6-b478baeecd70"
scope = f"openid+{client_id}+offline_access"

print("Testing ERCOT Azure B2C authentication endpoint...\n")
print(f"Endpoint: {endpoint}\n")

try:
    with httpx.Client(timeout=10.0) as client:
        # Build URL with query parameters (matching ERCOT documentation example)
        auth_url_with_params = (
            f"{endpoint}"
            f"?username={quote_plus(username)}"
            f"&password={quote_plus(password)}"
            f"&grant_type=password"
            f"&scope={quote_plus(scope)}"
            f"&client_id={client_id}"
            f"&response_type=id_token"
        )

        print("Testing authentication with query parameters in URL...")
        response = client.post(
            auth_url_with_params,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print("  ✓ SUCCESS! Authentication works.")
            try:
                data = response.json()
                # Check for access_token first (as per ERCOT example), then id_token
                token = data.get("access_token") or data.get("id_token")
                if token:
                    print(f"  Token received: {token[:30]}...")
                    print(f"  Token length: {len(token)} characters")
                    print(f"  Token type: {'access_token' if 'access_token' in data else 'id_token'}")
                else:
                    print(f"  Response data keys: {list(data.keys())}")
                    print(f"  Full response: {data}")
            except Exception as e:
                print(f"  Failed to parse JSON: {e}")
                print(f"  Response text: {response.text[:200]}")
        else:
            print("  ✗ Authentication failed")
            print(f"  Response: {response.text[:500]}")
        print()
except Exception as e:
    print(f"  Error: {e}\n")
    import traceback
    traceback.print_exc()

print("\nNote: The subscription key is used in API requests, not authentication.")
print("Make sure to include it in API request headers: Ocp-Apim-Subscription-Key")

