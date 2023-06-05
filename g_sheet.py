import os
import time
import psycopg2
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

# Retrieve the PostgreSQL connection details from environment variables
db_host = os.getenv('HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DATABASE')
db_user = os.getenv('USER')
db_password = os.getenv('PASSWORD')

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)

# Function to read Google Sheets and create a PostgreSQL table for each sheet
def read_google_sheets(sheet_id):
    cursor = conn.cursor()

    # Set the credentials and scope for accessing Google Sheets API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

    # Authorize the credentials and create a client
    client = gspread.authorize(credentials)

    while True:
        try:
            # Open the Google Spreadsheet by its ID
            spreadsheet = client.open_by_key(sheet_id)

            for worksheet in spreadsheet.worksheets():
                column_names = worksheet.row_values(1)

                # Remove any special characters from column names to make them valid for PostgreSQL
                valid_column_names = [name.lower().replace(' ', '_').replace('-', '_') for name in column_names]

                table_name = sheet_id

                # Create the PostgreSQL table if it doesn't exist
                create_table_query = f'CREATE TABLE IF NOT EXISTS "{table_name}" ('

                for column_name in valid_column_names:
                    create_table_query += f'"{column_name}" VARCHAR,'
                
                create_table_query = create_table_query.rstrip(',') + ');'

                cursor.execute(create_table_query)
                conn.commit()

                # Insert data from the worksheet into the PostgreSQL table
                all_values = worksheet.get_all_values()
                headers = all_values[0]  # Use original column names
                insert_query = f'INSERT INTO "{table_name}" ({", ".join(valid_column_names)}) VALUES ({", ".join(["%s"] * len(valid_column_names))})'

                for row in all_values[1:]:
                    cursor.execute(insert_query, row)
                    conn.commit()

            break

        except gspread.exceptions.SpreadsheetNotFound:
            print("Spreadsheet not found!")
            break

        except gspread.exceptions.APIError as e:
            print(f"APIError occurred: {e}")
            time.sleep(10)

    conn.close()

# Retrieve the spreadsheet ID from environment variables
spreadsheet_id = os.getenv('SPREADSHEET_ID')

# Call the function to read the Google Sheets and insert data into PostgreSQL tables
read_google_sheets(spreadsheet_id)
