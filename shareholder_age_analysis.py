import pandas as pd
import requests
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import re

# Load environment variables
load_dotenv()

# Configuration
API_TOKEN = os.getenv('PROFF_API_TOKEN', 'YOUR_API_TOKEN_HERE')
INPUT_FILE = 'companies.md'  # Changed to markdown file
OUTPUT_FILE = 'shareholders_with_age.xlsx'
COUNTRY = 'NO'  # Default to Norway

class ProffAPI:
    def __init__(self, token):
        self.token = token
        self.base_url = 'https://api.proff.no'
        self.headers = {
            'Authorization': f'Token {self.token}',
            'Accept': 'application/json'
        }
        self.call_count = 0  # Initialize call counter

    def get_company_owners(self, country, company_id):
        """Get real owners (ultimate beneficial owners) for a specific company."""
        self.call_count += 1  # Increment counter
        url = f"{self.base_url}/api/companies/owner/{country}/{company_id}"
        print(f"Making API request #{self.call_count} to: {url}")
        
        response = requests.get(url, headers=self.headers)
        print(f"Response status code: {response.status_code}")
        
        try:
            response_data = response.json()
            if response.status_code == 200:
                return response_data
            else:
                print(f"Error response: {response_data}")
                return None
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

def read_company_numbers(markdown_file):
    """Read organization numbers from markdown file."""
    org_numbers = []
    with open(markdown_file, 'r', encoding='utf-8') as f:
        for line in f:
            # Strip whitespace and get only digits
            number = ''.join(filter(str.isdigit, line.strip()))
            if len(number) == 9:  # Norwegian org numbers are 9 digits
                org_numbers.append(number)
    return org_numbers

def process_shareholders(api, org_numbers):
    """Process each company and get real shareholder information."""
    results = []
    
    for company_id in org_numbers:
        print(f"\nProcessing company ID: {company_id}")
        
        # Get real owners data
        company_data = api.get_company_owners(COUNTRY, company_id)
        
        if not company_data:
            print(f"No response data for company: {company_id}")
            continue
            
        company_name = company_data.get('Name', f"Company {company_id}")
        
        # Debug print to see the structure
        print(f"Company data for {company_name}:")
        print(json.dumps(company_data, indent=2))
            
        if 'Shareholders' not in company_data or not company_data['Shareholders']:
            print(f"No shareholders found for company: {company_id}")
            continue
            
        # Process each shareholder
        for shareholder in company_data['Shareholders']:
            # Get the shareholder name, trying different fields
            shareholder_name = (
                shareholder.get('NameFromShareholder') or 
                shareholder.get('nameFromShareholder') or 
                shareholder.get('NameFromRole') or 
                shareholder.get('nameFromRole')
            )
            
            # Get birth year, trying different fields
            birth_year = shareholder.get('BirthYear') or shareholder.get('birthYear')
            
            # Get ownership percentage
            ownership = shareholder.get('ShareInPercent') or shareholder.get('shareInPercent')
            
            results.append({
                'company_id': company_id,
                'company_name': company_name,
                'shareholder_name': shareholder_name,
                'birth_year': birth_year,
                'age': calculate_age(birth_year),
                'direct_ownership': shareholder.get('DirectOwnership') or shareholder.get('directOwnership'),
                'indirect_ownership': shareholder.get('IndirectOwnership') or shareholder.get('indirectOwnership'),
                'ownership_percentage': ownership,
                'country': shareholder.get('CountryCode') or shareholder.get('countryCode')
            })
            
            # Print debug info
            print(f"Added shareholder: {shareholder_name} ({ownership}% ownership)")
    
    return pd.DataFrame(results)

def main():
    # Check if API token is set
    if API_TOKEN == 'YOUR_API_TOKEN_HERE':
        print("Please set your API token in the .env file")
        return

    try:
        # Initialize API client
        api = ProffAPI(API_TOKEN)
        
        # Read organization numbers from markdown
        print(f"Reading organization numbers from: {INPUT_FILE}")
        org_numbers = read_company_numbers(INPUT_FILE)
        
        if not org_numbers:
            print("No organization numbers found in the markdown file!")
            return
            
        print(f"\nFound {len(org_numbers)} companies to process")
        
        # Process shareholders
        print("\nProcessing shareholders...")
        results_df = process_shareholders(api, org_numbers)
        
        if len(results_df) == 0:
            print("\nNo shareholder data found for any company!")
            return
            
        # Export results
        print(f"\nExporting {len(results_df)} shareholder records to: {OUTPUT_FILE}")
        results_df.to_excel(OUTPUT_FILE, index=False)
        
        print(f"\nProcessing completed successfully!")
        print(f"Total API calls made: {api.call_count}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 