import argparse
import requests
import json

# Script to test the user registration endpoint
# Usage: python test_register.py --base-url http://localhost:8000/api/v1 --email abc@gmail.com --password yourpassword

def main():
    parser = argparse.ArgumentParser(description="Test register endpoint")
    parser.add_argument("--base-url", required=True, help="Base URL of the API")
    parser.add_argument("--email", required=True, help="User email")
    parser.add_argument("--password", required=True, help="User password")

    args = parser.parse_args()

    url = f"{args.base_url}/auth/register"
    data = {
        "email": args.email,
        "password": args.password
    }

    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print("Response:")
        print(json.dumps(response.json(), indent=2))
    except requests.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
