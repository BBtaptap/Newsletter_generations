# tools.py (or wherever you want to keep this class)

import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict, Any
from googleapiclient.errors import HttpError # <--- ADD THIS LINE
from googleapiclient.discovery import build

class GoogleSheetsHelper:
    """
    A helper class to interact with Google Sheets using gspread,
    designed for direct calls from Python scripts.
    """

    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """
        Initializes the Google Sheets client and opens the target spreadsheet.

        Args:
            credentials_path: Path to the Google Service Account credentials JSON file.
            spreadsheet_id: The ID of the target Google Spreadsheet.
        """
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        print(f"[GS Init] Attempting init for sheet ID: {spreadsheet_id}") # DEBUG
        self.spreadsheet_id = spreadsheet_id
        self.creds = None  # Initialize attributes
        self.service = None # Initialize attributes

        try:
            print(f"[GS Init] Loading credentials from: {credentials_path}") # DEBUG
            self.creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
            print(f"[GS Init] Credentials loaded successfully? {'Yes' if self.creds else 'No'}") # DEBUG

            if not self.creds:
                 raise ValueError("Failed to load credentials object.") # Explicit check

            print("[GS Init] Building Google Sheets service...") # DEBUG
            self.service = build('sheets', 'v4', credentials=self.creds)
            print(f"[GS Init] Google Sheets service built successfully? {'Yes' if self.service else 'No'}") # DEBUG

            if not self.service:
                 raise ValueError("Failed to build Google Sheets service object.") # Explicit check

            # Only print success if BOTH steps above actually worked
            print("[GS Init] --- Google Sheets API Service Initialized Successfully ---")

        except FileNotFoundError:
            print(f"[GS Init] ERROR: Credentials file not found at {credentials_path}")
            # Re-raise the exception so the calling code knows init failed
            raise
        except Exception as e:
            print(f"[GS Init] ERROR: Exception during credential loading or service building: {e}")
            # Re-raise the exception
            raise
        finally:
            # This block executes regardless of exceptions
            print(f"[GS Init] Exiting __init__. self.service is type: {type(self.service)}") # DEBUG check

    def append_data_row(self, sheet_name: str, data_dict: dict, column_order: list) -> int | None:
        """
        Appends a single row of data based on a dictionary and column order.
        Returns the 1-based index of the newly appended row, or None on failure.
        """
        try:
            # Ensure all values are strings for Sheets API compatibility
            values_to_append = [str(data_dict.get(col_header, "")) for col_header in column_order]

            body = {
                'values': [values_to_append]
            }
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"'{sheet_name}'!A:A", # Append based on first column
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()

            # print(f"Append result: {result}") # Optional debug print
            updated_range = result.get('updates', {}).get('updatedRange')

            if updated_range:
                try:
                    # Extract row number robustly
                    range_part = updated_range.split('!')[1]
                    start_cell = range_part.split(':')[0]
                    row_index_str = ''.join(filter(str.isdigit, start_cell))
                    if row_index_str:
                        row_index = int(row_index_str)
                        # print(f"Data successfully appended to sheet '{sheet_name}'. Determined row index: {row_index}") # More precise success message
                        return row_index # <<< RETURN THE INTEGER ROW INDEX
                    else:
                        print(f"Error: Could not parse row index from start cell '{start_cell}' in range '{updated_range}'.")
                        return None
                except (IndexError, ValueError) as parse_error:
                    print(f"Error parsing updated range '{updated_range}': {parse_error}")
                    return None
            else:
                 print("Error: Append result did not contain updated range information.")
                 return None

        except HttpError as error:
            print(f"An API error occurred during append: {error}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during append: {e}")
            return None

    def update_cell(self, sheet_name: str, row_index: int, col_index: int, value: str) -> bool:
        """
        Updates a single cell value.
        row_index: 1-based row number.
        col_index: 0-based column number.
        Returns True on success, False on failure.
        """
        if not isinstance(row_index, int) or row_index < 1:
            print(f"Error: Invalid row_index '{row_index}'. Must be a positive integer.")
            return False
        if not isinstance(col_index, int) or col_index < 0:
             print(f"Error: Invalid col_index '{col_index}'. Must be a non-negative integer.")
             return False

        try:
            col_letter = col_index_to_a1(col_index) # Uses the helper function
            target_range = f"'{sheet_name}'!{col_letter}{row_index}"
            print(f"Attempting to update cell: {target_range} with value type: {type(value)}")

            body = {
                'values': [[str(value)]] # Ensure value is string, nested in two lists
            }
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=target_range,
                valueInputOption='USER_ENTERED', # Or 'RAW' if you don't want interpretation
                body=body
            ).execute()

            print(f"Update result: {result}")
            updated_cells = result.get('updatedCells')
            # Check if the update happened, >= 1 is safer
            if updated_cells is not None and updated_cells >= 1:
                print(f"Successfully updated cell {target_range}.")
                return True
            else:
                # Sometimes the API might not return updatedCells but still works, log carefully
                print(f"Warning/Info: Update executed for {target_range}, but API reported updatedCells: {updated_cells}. Assuming success.")
                return True # Be optimistic, but monitor logs

        except HttpError as error:
            print(f"An API error occurred during update of {target_range}: {error}")
            # print(f"Details: {error.content}") # Uncomment for more debug info if needed
            return False
        except Exception as e:
            print(f"An unexpected error occurred during update of {target_range}: {e}")
            return False

    def list_sheets(self):
        """Lists the names of all sheets (tabs) in the spreadsheet."""
        try:
            return [sheet.title for sheet in self.spreadsheet.worksheets()]
        except Exception as e:
            raise RuntimeError(f"Error listing worksheets: {e}")