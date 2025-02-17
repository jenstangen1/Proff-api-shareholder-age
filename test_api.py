import requests
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configuration
API_TOKEN = os.getenv('PROFF_API_TOKEN')
TEST_ORG_NUMBER = "917251770"
COUNTRY = 'NO'

def test_api():
    if not API_TOKEN:
        print("Error: No API token found in .env file")
        return

    # Print token for verification (first few characters)
    print(f"Using API token: {API_TOKEN[:10]}...")

    # Setup API request
    url = f"https://api.proff.no/api/companies/owner/{COUNTRY}/{TEST_ORG_NUMBER}"
    headers = {
        'Authorization': f'Token {API_TOKEN}',
        'Accept': 'application/json'
    }

    print(f"\nMaking API request to: {url}")
    print(f"Headers: {headers}")

    try:
        response = requests.get(url, headers=headers)
        print(f"\nResponse status code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nAPI call successful! Response data:")
            print(json.dumps(data, indent=2))
            
            if 'shareholders' in data:
                print(f"\nFound {len(data['shareholders'])} shareholders")
                for shareholder in data['shareholders']:
                    print(f"- {shareholder.get('nameFromShareholder') or shareholder.get('nameFromRole')}")
            else:
                print("\nNo shareholders found in response")
        else:
            print(f"\nError response: {response.text}")
            
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    test_api() 