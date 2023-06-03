import os
import time
import gspread
from gspread.exceptions import SpreadsheetNotFound, APIError
from oauth2client.service_account import ServiceAccountCredentials

from dotenv import load_dotenv

load_dotenv()

sheet_link = os.getenv('GOOGLE_SHEET')

def sheet():
    # Set the credentials and scope for accessing Google Sheets API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

    # Authorize the credentials and create a client
    client = gspread.authorize(credentials)

    while True:
        try:
            # Open the Google Spreadsheet by its title or URL
            test = sheet_link
            spreadsheet_id = test.split('/')[-2]

            # Get the first worksheet from the spreadsheet
            spreadsheet = client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.get_worksheet(0)

            # Get all values in column N and corresponding row values
            column_N = worksheet.col_values(18)  # Assuming column N is the 14th column
            all_rows = worksheet.get_all_values()

            # Filter rows that contain "violation" in column N
            filtered_rows = [row for row, value in zip(all_rows, column_N) if value.lower() == "violation"]

            # Combine values of columns F and G into a single variable
            combined_values = []

            # Print the filtered rows
            for row in filtered_rows:
                # print(row)
                # Get the values of columns F and G
                column_f = row[5]  # Column F (index 5) Title
                column_g = row[6]  # Column G (index 6) Body

                combined_value = f"{column_f}. {column_g}"
                print(column_g)
                return column_g
            
                # combined_values.append(combined_value)

                # Print the combined values
                # for value in combined_values:
                #     print(value)

                # break

            # Count the number of filtered rows
            # row_count = len(filtered_rows)

            # Print the count
            # print("Number of rows displayed:", row_count)

            break

        except SpreadsheetNotFound:
            print("Spreadsheet not found!")
            break  # Break the loop if the spreadsheet is not found (optional)

        except APIError as e:
            # print(f"APIError occurred: {e}")
            print(f"APIError occurred:")
            # Add a delay before retrying (optional)
            time.sleep(10)

# sheet()