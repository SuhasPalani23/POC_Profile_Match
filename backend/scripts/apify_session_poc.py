import os
import json
import requests
from dotenv import load_dotenv

# Load Apify key from the main project .env
dotenv_path = os.path.join(os.path.dirname(__file__), '../../.env')
load_dotenv(dotenv_path)

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
# Apify actor often used for LinkedIn scraping using session cookies:
ACTOR_ID = "curious_coder/linkedin-profile-scraper" 

def run_session_scrape_poc(profile_url, li_at_cookie):
    """
    This POC demonstrates how to scrape a LinkedIn profile using a provided session cookie
    (li_at token) directly via the Apify API, without requiring the user to authenticate
    via OAuth on our platform.
    
    In production, the `li_at_cookie` would be a system-level or rotating headless account cookie.
    """
    print(f"Starting headless session scrape for: {profile_url}")
    print("Authenticating with Apify using Session Cookie approach...")
    
    url = f"https://api.apify.com/v2/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
    
    # Payload typical for a LinkedIn scraper accepting a session cookie
    payload = {
        "urls": [profile_url],
        "cookie": [
            {
                "name": "li_at",
                "value": li_at_cookie,
                "domain": ".linkedin.com"
            }
        ]
    }
    
    print("Initiating run...")
    response = requests.post(url, json=payload)
    
    if response.status_code not in (200, 201):
        print(f"Failed to start actor. Status Code: {response.status_code}")
        print(response.text)
        return
        
    run_data = response.json()
    run_id = run_data['data']['id']
    default_kv_store_id = run_data['data']['defaultKeyValueStoreId']
    default_dataset_id = run_data['data']['defaultDatasetId']
    
    print(f"Run {run_id} started successfully!")
    print(f"To check status, visit: https://console.apify.com/actors/runs/{run_id}")
    print("Once complete, data will be available in Dataset ID:", default_dataset_id)
    print("\n[!] This demonstrates the mechanism the CTO requested: pure background scraping using a system session cookie.")

if __name__ == "__main__":
    if not APIFY_TOKEN:
        print("Error: APIFY_TOKEN not found in .env. Please ensure it is set.")
    else:
        print("Apify Key loaded successfully.")
        
        # NOTE: For this POC to actually pull data, a valid 'li_at' cookie from a real LinkedIn 
        # session is required. Replace the mock value below with a real cookie if testing.
        MOCK_LINKEDIN_URL = "https://www.linkedin.com/in/williamhgates/"
        MOCK_LI_AT_COOKIE = "CHANGE_ME_TO_A_REAL_LI_AT_COOKIE"
        
        print(f"WARNING: Script requires a valid li_at cookie. Currently using: {MOCK_LI_AT_COOKIE}")
        print("To run a live test, replace MOCK_LI_AT_COOKIE with a real token from your browser.\n")
        
        # run_session_scrape_poc(MOCK_LINKEDIN_URL, MOCK_LI_AT_COOKIE)
        
        print("POC Script ready. Review the code to see how system-level headless scraping is implemented.")
