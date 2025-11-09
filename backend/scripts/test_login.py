import argparse
import json

import requests

# Script to test the user login endpoint
# Usage: python test_login.py --base-url http://localhost:8000/api/v1 --email abc@gmail.com --password yourpassword

def main():
    parser = argparse.ArgumentParser(description="Test login endpoint")
    parser.add_argument("--base-url", required=True, help="Base URL of the API")
    parser.add_argument("--email", required=True, help="User email")
    parser.add_argument("--password", required=True, help="User password")

    args = parser.parse_args()

    url = f"{args.base_url}/auth/login"
    data = {
        "email": args.email,
        "password": args.password
    }

    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))

        # If login successful, print the access token separately for easy copying
        if response.status_code == 200:
            response_data = response.json()
            if "data" in response_data and "access_token" in response_data["data"]:
                print("\n" + "="*50)
                print("Access Token:")
                print(response_data["data"]["access_token"])
                print("="*50)
    except requests.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

