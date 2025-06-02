import requests
import json
import datetime
import os
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration (Read from environment variables) ---
# These variables will now be loaded from your .env file
# If a variable is not found in .env or system environment, it will use the default value provided here.
# For production, ensure these are always set in your deployment environment.
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_ORGANIZATION_ID = os.getenv("ZOHO_ORGANIZATION_ID")
ZOHO_REDIRECT_URI = os.getenv("ZOHO_REDIRECT_URI", "https://localhost") # Default for development
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")

# Zoho Books Account IDs (replace with your actual IDs from Zoho Books)
# You can get these by inspecting your Chart of Accounts in Zoho Books or using the Zoho Books API.
ZOHO_ACCOUNTS_PAYABLE_ACCOUNT_ID = os.getenv("ZOHO_ACCOUNTS_PAYABLE_ACCOUNT_ID")
ZOHO_EDMUND_OPIYO_OWNERS_EQUITY_ACCOUNT_ID = os.getenv("ZOHO_EDMUND_OPIYO_OWNERS_EQUITY_ACCOUNT_ID")
ZOHO_DEFAULT_CURRENCY_ID = os.getenv("ZOHO_DEFAULT_CURRENCY_ID") # e.g., for KES

# --- API Endpoints ---
ZOHO_OAUTH_URL = "https://accounts.zoho.com/oauth/v2/token"
ZOHO_BOOKS_API_BASE_URL = "https://books.zoho.com/api/v3"

# --- Validation for critical environment variables ---
# It's good practice to ensure critical variables are loaded.
if not all([ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_ORGANIZATION_ID, ZOHO_REFRESH_TOKEN,
            ZOHO_ACCOUNTS_PAYABLE_ACCOUNT_ID, ZOHO_EDMUND_OPIYO_OWNERS_EQUITY_ACCOUNT_ID,
            ZOHO_DEFAULT_CURRENCY_ID]):
    print("Error: One or more critical Zoho Books environment variables are missing.")
    print("Please ensure ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_ORGANIZATION_ID, ZOHO_REFRESH_TOKEN,")
    print("ZOHO_ACCOUNTS_PAYABLE_ACCOUNT_ID, ZOHO_EDMUND_OPIYO_OWNERS_EQUITY_ACCOUNT_ID,")
    print("and ZOHO_DEFAULT_CURRENCY_ID are set in your .env file or environment.")
    exit(1) # Exit if essential variables are not set

def refresh_access_token(refresh_token):
    """Refreshes the Zoho Books access token using the refresh token."""
    print("Attempting to refresh access token...")
    payload = {
        'refresh_token': refresh_token,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'redirect_uri': ZOHO_REDIRECT_URI,
        'grant_type': 'refresh_token',
    }
    try:
        response = requests.post(ZOHO_OAUTH_URL, data=payload)
        response.raise_for_status() # Raise an exception for bad status codes
        token_data = response.json()
        new_access_token = token_data.get('access_token')
        new_expires_in = token_data.get('expires_in') # Time in seconds until expiry

        if new_access_token:
            print(f"Access token refreshed successfully. Expires in {new_expires_in} seconds.")
            return new_access_token
        else:
            print(f"Access token not found in response: {token_data}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error refreshing access token: {e}")
        print(f"Response: {response.text if response else 'No response'}")
        return None

def create_journal_entry_in_zoho_books(access_token, payment_data):
    """
    Creates a journal entry in Zoho Books based on payment data.

    Args:
        access_token (str): The current valid Zoho Books API access token.
        payment_data (dict): A dictionary containing payment details like:
                             - 'amount': float
                             - 'vendor_name': str
                             - 'bill_reference': str (optional)
                             - 'payment_date': str (YYYY-MM-DD)
                             - 'is_accounts_payable_payment': bool (True if paying a bill, False for direct expense)
                             - 'direct_expense_account_id': str (if is_accounts_payable_payment is False)
    Returns:
        dict: The response from Zoho Books if successful, None otherwise.
    """
    journal_entry_url = f"{ZOHO_BOOKS_API_BASE_URL}/journalentries"
    
    amount = payment_data['amount']
    vendor_name = payment_data['vendor_name']
    bill_reference = payment_data.get('bill_reference', 'N/A')
    payment_date = payment_data['payment_date']
    is_ap_payment = payment_data.get('is_accounts_payable_payment', True)
    direct_expense_account_id = payment_data.get('direct_expense_account_id')

    # Determine debit account based on payment type
    debit_account_id = None
    notes_prefix = ""

    if is_ap_payment:
        debit_account_id = ZOHO_ACCOUNTS_PAYABLE_ACCOUNT_ID
        notes_prefix = f"Payment for bill {bill_reference} to {vendor_name}"
    elif direct_expense_account_id:
        debit_account_id = direct_expense_account_id
        notes_prefix = f"Direct expense payment to {vendor_name}"
    else:
        print("Error: Could not determine debit account. 'is_accounts_payable_payment' is False but 'direct_expense_account_id' is not provided.")
        return None

    if not debit_account_id:
        print("Error: Debit account ID is missing after determination logic.")
        return None

    # Construct the journal entry payload
    payload = {
        "journal_date": payment_date,
        "currency_id": ZOHO_DEFAULT_CURRENCY_ID,
        "reference_number": f"PAY-{bill_reference or datetime.datetime.now().strftime('%Y%m%d%H%M%S')}", # Generate a unique ref
        "notes": f"{notes_prefix}, funded by owner. Amount: {amount:.2f}",
        "line_items": [
            {
                "account_id": debit_account_id,
                "debit": amount,
                "description": f"Debit for {vendor_name} ({bill_reference})"
            },
            {
                "account_id": ZOHO_EDMUND_OPIYO_OWNERS_EQUITY_ACCOUNT_ID,
                "credit": amount,
                "description": "Credit for owner's contribution"
            }
        ]
    }

    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "X-Crm-Org-Id": ZOHO_ORGANIZATION_ID,
        "Content-Type": "application/json"
    }

    print(f"Sending journal entry request to Zoho Books for amount: {amount}...")
    try:
        response = requests.post(journal_entry_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)

        journal_entry_response = response.json()
        if journal_entry_response and journal_entry_response.get('journalentry') and journal_entry_response['journalentry'].get('journal_id'):
            print(f"Journal entry created successfully! Journal ID: {journal_entry_response['journalentry']['journal_id']}")
            return journal_entry_response
        else:
            print(f"Unexpected response structure from Zoho Books: {journal_entry_response}")
            return None

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error creating journal entry: {e}")
        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request Error creating journal entry: {e}")
        return None

# --- Main Automation Logic ---
def automate_payment_journal_entry(payment_details):
    """
    Orchestrates the automation process for a single payment.
    """
    # In a real system, the refresh token would be loaded from secure storage
    # and potentially updated if Zoho issues a new one (though less common for refresh tokens).
    current_refresh_token = ZOHO_REFRESH_TOKEN 

    # 1. Get/Refresh Access Token
    current_access_token = refresh_access_token(current_refresh_token)
    if not current_access_token:
        print("Failed to get access token. Cannot proceed with journal entry.")
        return False

    # 2. Create Journal Entry
    journal_entry_result = create_journal_entry_in_zoho_books(current_access_token, payment_details)

    if journal_entry_result:
        journal_id = journal_entry_result['journalentry']['journal_id']
        print(f"Automation successful! Payment processed for {payment_details['amount']}. Journal ID: {journal_id}")
        # In a real system, you would now:
        # - Store this journal_id with your payment record in your source system.
        # - Log the successful transaction.
        return True
    else:
        print("Automation failed for this payment.")
        # In a real system, you would:
        # - Log the failure details.
        # - Trigger an alert for manual review.
        return False

# --- Simulate a Payment Event (This is where your actual payment system would feed data) ---
if __name__ == "__main__":
    # Example 1: Payment for a previously billed item (debit Accounts Payable)
    simulated_payment_1 = {
        'amount': 50000.00,
        'vendor_name': 'Safeguard Security',
        'bill_reference': 'INV-SEC-2025-001',
        'payment_date': '2025-06-01',
        'is_accounts_payable_payment': True,
        'direct_expense_account_id': None # Not used here
    }

    # Example 2: Direct expense payment (debit a specific expense account, assuming no prior bill)
    # This requires YOUR_OFFICE_SUPPLIES_EXPENSE_ACCOUNT_ID to be set in your .env
    simulated_payment_2 = {
        'amount': 2500.00,
        'vendor_name': 'Office Mart',
        'bill_reference': 'PO-OM-789', # Still good to have a reference
        'payment_date': '2025-06-01',
        'is_accounts_payable_payment': False,
        'direct_expense_account_id': os.getenv("YOUR_OFFICE_SUPPLIES_EXPENSE_ACCOUNT_ID")
    }

    # Run the automation for the first simulated payment
    print("\n--- Processing Simulated Payment 1 (AP Debit) ---")
    automate_payment_journal_entry(simulated_payment_1)

    # Run the automation for the second simulated payment
    print("\n--- Processing Simulated Payment 2 (Direct Expense Debit) ---")
    if simulated_payment_2['direct_expense_account_id']:
        automate_payment_journal_entry(simulated_payment_2)
    else:
        print("Skipping Simulated Payment 2: YOUR_OFFICE_SUPPLIES_EXPENSE_ACCOUNT_ID not set in .env")

    print("\nAutomation process finished.")
