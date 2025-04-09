import os.path
import pickle # Using pickle for token storage (consider more secure alternatives for production)

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- Configuration ---
# If modifying these scopes, delete the file token.pickle.
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets.readonly', # Read from Sheets
    'https://www.googleapis.com/auth/documents',           # Read/Write Docs
    'https://www.googleapis.com/auth/drive'                # Copy files (Docs)
]

# --- !!! UPDATE THESE VALUES !!! ---
SPREADSHEET_ID = '16o88VRyZLcAa3ZwC-kGRU2QJIj-Rad4FQIKmYcY5j-o'  # Get from Sheet URL
DATA_RANGE_NAME = 'Sheet1!A1:Z'        # e.g., 'Sheet1!A1:E' - Must include header row
TEMPLATE_DOC_ID = '1EcGD6mm85NCfmEQ0M0PmCO3rPUpcYNr7NVYsflzmOHg' # Get from Template Doc URL
OUTPUT_FOLDER_ID = None # Optional: Google Drive Folder ID to save generated docs
                        # If None, they save in your root 'My Drive'
NEW_DOC_NAME_COLUMN = 'Name' # Optional: Column header in your sheet to use for the new doc's name
                             # If None or column not found, uses a generic name.
# --- End Configuration ---

TOKEN_FILE = 'token.pickle' # Stores user's access/refresh tokens
CREDENTIALS_FILE = 'client_secrets.json' # Downloaded OAuth credentials

def authenticate():
    """Shows basic usage of the Google APIs authentication."""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'rb') as token:
                creds = pickle.load(token)
        except (pickle.UnpicklingError, EOFError):
            print(f"Error loading token file: {TOKEN_FILE}. Deleting and re-authenticating.")
            os.remove(TOKEN_FILE) # Delete corrupted token
            creds = None

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        # --- Add these lines for debugging ---
        print(f"Attempting to load credentials from: {os.path.abspath(CREDENTIALS_FILE)}")
        if not os.path.exists(CREDENTIALS_FILE):
             print(f"ERROR: Credentials file '{CREDENTIALS_FILE}' not found.")
             print("Please download it from Google Cloud Console and place it here.")
             return None
        else:
             print(f"Credentials file found.")


        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES) # This is line 63 in your original trace
        creds = flow.run_local_server(port=0)
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Failed to refresh token: {e}")
                print("Attempting full re-authentication...")
                # If refresh fails, force re-authentication by removing token file
                if os.path.exists(TOKEN_FILE):
                    os.remove(TOKEN_FILE)
                creds = None # Ensure re-auth flow runs below
        # Only run the flow if creds are still None (initial auth or failed refresh)
        if not creds:
            if not os.path.exists(CREDENTIALS_FILE):
                 print(f"ERROR: Credentials file '{CREDENTIALS_FILE}' not found.")
                 print("Please download it from Google Cloud Console and place it here.")
                 return None
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # Specify redirect_uri for desktop app flow if needed, otherwise defaults usually work
            # Example: flow.run_local_server(port=0) might require specifying redirect_uri in Cloud Console
            creds = flow.run_local_server(port=0) # Runs local server for auth code capture

        # Save the credentials for the next run
        try:
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(creds, token)
        except Exception as e:
            print(f"Error saving token file: {e}")

    if not creds:
         print("Failed to obtain credentials.")
         return None

    print("Authentication successful.")
    return creds

def main():
    """Reads data from Sheet, copies template Doc, and replaces placeholders."""
    creds = authenticate()
    if not creds:
        return # Stop if authentication failed

    try:
        # Build API services
        sheets_service = build('sheets', 'v4', credentials=creds)
        docs_service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        # --- 1. Read Data From Google Sheet ---
        sheet = sheets_service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                    range=DATA_RANGE_NAME).execute()
        values = result.get('values', [])

        if not values:
            print('No data found in the sheet.')
            return

        headers = values[0] # First row is header
        data_rows = values[1:] # All other rows are data

        print(f"Found {len(data_rows)} data rows in the sheet.")

        # --- 2. Process Each Data Row ---
        for i, row in enumerate(data_rows):
            # Create a dictionary for the current row {header: value}
            row_data = {}
            for j, header in enumerate(headers):
                if j < len(row):
                    row_data[header] = row[j]
                else:
                    row_data[header] = "" # Handle empty cells or rows shorter than header

            print(f"\nProcessing row {i+1}...") # User-friendly row number

            # --- 3. Copy the Template Document ---
            # Determine the name for the new document
            new_doc_name = f"Generated Doc - Row {i+2}" # Default name (Sheet row index + 2)
            if NEW_DOC_NAME_COLUMN and NEW_DOC_NAME_COLUMN in row_data and row_data[NEW_DOC_NAME_COLUMN]:
                new_doc_name = str(row_data[NEW_DOC_NAME_COLUMN]) # Use value from specified column

            copy_metadata = {'name': new_doc_name}
            if OUTPUT_FOLDER_ID:
                copy_metadata['parents'] = [OUTPUT_FOLDER_ID]

            try:
                copied_file = drive_service.files().copy(
                    fileId=TEMPLATE_DOC_ID,
                    body=copy_metadata,
                    fields='id, name' # Request only needed fields
                ).execute()
                new_doc_id = copied_file.get('id')
                print(f"  Copied template to new document: '{copied_file.get('name')}' (ID: {new_doc_id})")
            except HttpError as error:
                print(f"  An error occurred copying the template: {error}")
                print(f"  Skipping row {i+1}.")
                continue # Skip to the next row if copy fails

            # --- 4. Prepare Placeholder Replacements ---
            requests = []
            for header, value in row_data.items():
                placeholder = f"{{{{{header}}}}}" # Format as {{HeaderName}}
                # Ensure value is a string for replacement
                replacement_value = str(value)

                requests.append({
                    'replaceAllText': {
                        'containsText': {
                            'text': placeholder,
                            'matchCase': False # Case-insensitive matching for {{Placeholder}}
                        },
                        'replaceText': replacement_value,
                    }
                })

            # --- 5. Execute Replacements in the New Document ---
            if requests:
                try:
                    print(f"  Replacing {len(requests)} placeholders...")
                    docs_service.documents().batchUpdate(
                        documentId=new_doc_id,
                        body={'requests': requests}
                    ).execute()
                    print("  Replacements complete.")
                except HttpError as error:
                    print(f"  An error occurred replacing text: {error}")
                    # Consider deleting the partially generated file or logging the error
            else:
                print("  No placeholders found matching sheet headers for this row.")

        print("\nScript finished.")

    except HttpError as err:
        print(f"An API error occurred: {err}")
        if err.resp.status == 403:
             print("Ensure Google Docs, Sheets, and Drive APIs are enabled in your Cloud project.")
        if err.resp.status == 401:
             print("Authentication error. Try deleting 'token.pickle' and re-running.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()