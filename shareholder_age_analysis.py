import pandas as pd
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Configuration
API_TOKEN = os.getenv('PROFF_API_TOKEN', 'YOUR_API_TOKEN_HERE')
INPUT_FILE = 'companies.xlsx'  # Replace with your input Excel file name
OUTPUT_FILE = 'shareholders_with_age.xlsx'
COUNTRY = 'NO'  # Default to Norway, change as needed

class ProffAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = 'https://api.proff.no'  # Updated base URL
        self.headers = {
            'Authorization': f'Token {self.token}',
            'Accept': 'application/json'
        }

    def get_company_owners(self, country, company_id):
        """Get owners for a specific company."""
        url = f"{self.base_url}/api/shareholders/eniropro/{country}/owners/{company_id}"
        print(f"Making API request to: {url}")
        print(f"Headers: {self.headers}")
        response = requests.get(url, headers=self.headers)
        print(f"Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Response data: {json.dumps(response_data, indent=2)}")
            return response_data
        except Exception as e:
            print(f"Error parsing response: {str(e)}")
            print(f"Raw response: {response.text}")
            return None

def calculate_age(birth_year):
    """Calculate age from birth year."""
    if not birth_year:
        return None
    current_year = datetime.now().year
    try:
        birth_year = int(birth_year)
        return current_year - birth_year
    except (ValueError, TypeError):
        return None

def process_shareholders(api, df):
    """Process each company and get shareholder information."""
    results = []
    
    # Get the first column name (which contains the org numbers)
    org_number_column = df.columns[0]
    
    for index, row in df.iterrows():
        company_id = str(row[org_number_column])
        company_name = "Company " + company_id  # Since we don't have company names in the Excel
        
        print(f"\nProcessing company: {company_name} (ID: {company_id})")
        
        # Get shareholders data
        shareholders_data = api.get_company_owners(COUNTRY, company_id)
        
        if not shareholders_data:
            print(f"No response data for company: {company_id}")
            continue
            
        if 'relations' not in shareholders_data:
            print(f"No 'relations' found in response for company: {company_id}")
            print(f"Available keys in response: {shareholders_data.keys()}")
            continue
            
        if not shareholders_data['relations']:
            print(f"Empty relations list for company: {company_id}")
            continue
            
        # Process each shareholder
        for shareholder in shareholders_data['relations']:
            results.append({
                'company_id': company_id,
                'company_name': company_name,
                'shareholder_name': shareholder.get('name'),
                'birth_year': shareholder.get('birthYear'),
                'age': calculate_age(shareholder.get('birthYear')),
                'entity_type': shareholder.get('entityType'),
                'ownership_percentage': shareholder.get('sharePercentage'),
                'country': shareholder.get('country')
            })
    
    return pd.DataFrame(results)

def main():
    # Check if API token is set
    if API_TOKEN == 'YOUR_API_TOKEN_HERE':
        print("Please set your API token in the .env file")
        return

    try:
        # Initialize API client
        api = ProffAPI(API_TOKEN)
        
        # Read input Excel file
        print(f"Reading input file: {INPUT_FILE}")
        df = pd.read_excel(INPUT_FILE)
        
        # Debug print
        print("\nDataFrame Info:")
        print(df.info())
        print("\nFirst few rows:")
        print(df.head())
        
        # Process shareholders
        print("\nProcessing shareholders...")
        results_df = process_shareholders(api, df)
        
        if len(results_df) == 0:
            print("\nNo shareholder data found for any company!")
            return
            
        # Export results
        print(f"\nExporting {len(results_df)} shareholder records to: {OUTPUT_FILE}")
        results_df.to_excel(OUTPUT_FILE, index=False)
        
        print("Processing completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 