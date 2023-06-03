import time
import gspread
from gspread.exceptions import SpreadsheetNotFound, APIError

from oauth2client.service_account import ServiceAccountCredentials

def sheet():
    # Set the credentials and scope for accessing Google Sheets API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

    # Authorize the credentials and create a client
    client = gspread.authorize(credentials)

    while True:
        try:
            # Open the Google Spreadsheet by its title or URL
            test = 'https://docs.google.com/spreadsheets/d/10Bf-QgEkv0OGnWgBkWSF804Fc0iRhPPnDHtE1-9O76w/edit?usp=sharing'
            spreadsheet_id = test.split('/')[-2]

            # Get the first worksheet from the spreadsheet
            spreadsheet = client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.get_worksheet(0)
            print(spreadsheet)
            print(worksheet)
            # Print the spreadsheet title
            print("Spreadsheet Title:", spreadsheet.title)

            # Print the worksheet title
            print("Worksheet Title:", worksheet.title)

            # Get all values in column N and corresponding row values
            column_N = worksheet.col_values(14)  # Assuming column N is the 14th column
            all_rows = worksheet.get_all_values()

            # Filter rows that contain "violation" in column N
            filtered_rows = [row for row, value in zip(all_rows, column_N) if value.lower() == "violation"]

            # Print the filtered rows
            for row in filtered_rows:
                print(row)

            # Count the number of filtered rows
            row_count = len(filtered_rows)

            # Print the count
            print("Number of rows displayed:", row_count)

            break

        except SpreadsheetNotFound:
            print("Spreadsheet not found!")
            break  # Break the loop if the spreadsheet is not found (optional)

        except APIError as e:
            # print(f"APIError occurred: {e}")
            print(f"APIError occurred:")
            # Add a delay before retrying (optional)
            time.sleep(10)
    

sheet()
