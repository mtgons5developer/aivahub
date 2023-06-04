import os
import psycopg2
import gspread
from oauth2client.service_account import ServiceAccountCredentials

from dotenv import load_dotenv

load_dotenv()

sheet_link = os.getenv('GOOGLE_SHEET')
host = os.getenv('HOST')
database = os.getenv('DATABASE')
user = os.getenv('USER')
password = os.getenv('PASSWORD')

# Define the scope and credentials to access the Google Sheets API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

# Create a client to interact with the Google Sheets API
client = gspread.authorize(credentials)

# Open the Google Sheet by its title or URL
test = sheet_link #admin
spreadsheet_id = test.split('/')[-2]

# Get the first worksheet from the spreadsheet
spreadsheet = client.open_by_key(spreadsheet_id)
worksheet = spreadsheet.get_worksheet(0)

# Establish a connection to the PostgreSQL database
conn = psycopg2.connect(
    host=host,
    database=database,
    user=user,
    password=password
)

try:
    # Create a cursor object to execute SQL queries
    cur = conn.cursor()
    
    # Get all the values from the sheet
    data = worksheet.get_all_values()
    
    # Check if the table exists
    cur.execute("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'review_data_admin')")
    table_exists = cur.fetchone()[0]

    if not table_exists:
        # Create the table if it doesn't exist
        create_table_query = """
        CREATE TABLE review_data_admin (
            -- define the table columns here
            id serial PRIMARY KEY,
            date text,
            author text,
            verified VARCHAR(10),
            helpful VARCHAR(10),
            title TEXT,
            body TEXT,
            gpt_status VARCHAR(255),
            gpt_reason VARCHAR(255),
            ben_analysis TEXT,
            paul_analysis TEXT,
            patrick_analysis TEXT,
            drew_analysis TEXT,
            rating INTEGER,
            images TEXT,
            videos TEXT,
            url TEXT,
            variation VARCHAR(255),
            style TEXT
        );
        """
        cur.execute(create_table_query)
        conn.commit()

    # Iterate over the rows and insert data into PostgreSQL
    for row in data:
        # Skip the header row
        if row[0] == 'id':
            continue

        insert_query = "INSERT INTO review_data_admin (date, author, verified, helpful, title, body, gpt_status, gpt_reason, ben_analysis, paul_analysis, patrick_analysis, drew_analysis, rating, images, videos, url, variation, style) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

        # Extract the values from the row
        col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, col13, col14, col15, col16, col17, col18 = row

        # Convert the rating value to an integer if needed
        rating = int(col8) if col8.isdigit() else None

        # Execute the INSERT query
        cur.execute(insert_query, (col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, rating, col14, col15, col16, col17, col18))

    # Commit the changes to the database
    conn.commit()

    # Close the cursor
    cur.close()

except psycopg2.Error as e:
    print("Error connecting to PostgreSQL:", e)

finally:
    # Close the connection
    if conn is not None:
        conn.close()

# try:
#     # # Create a cursor object to execute SQL queries
#     cur = conn.cursor()
    
#     # Get all the values from the sheet
#     data = worksheet.get_all_values()

#     insert_query = "INSERT INTO review_data_admin (date, author, verified, helpful, title, body, gpt_status, gpt_reason, ben_analysis, paul_analysis, patrick_analysis, drew_analysis, rating, images, videos, url, variation, style) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"

#     # Iterate over the rows and insert data into PostgreSQL
#     for row in data:
#         # Skip the header row
#         if row[0] == 'id':
#             continue

#         # Extract the values from the row
#         col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, col13, col14, col15, col16, col17, col18 = row

#         # Convert the rating value to an integer if needed
#         rating = int(col8) if col8.isdigit() else None

#         # Execute the INSERT query
#         cur.execute(insert_query, (col1, col2, col3, col4, col5, col6, col7, col8, col9, col10, col11, col12, rating, col14, col15, col16, col17, col18))

#     # Commit the changes to the database
#     conn.commit()

#     # Close the cursor
#     cur.close()
#     conn.close()

# except psycopg2.Error as e:
#     print("Error connecting to PostgreSQL:", e)

# finally:
#     # Close the connection
#     conn.close()

quit()

# Define the SQL INSERT statement
# insert_query = "INSERT INTO <table_name> (col1, col2, ..., col18) VALUES (%s, %s, ..., %s)"
insert_query = "INSERT INTO review_data_gpt (date, author, verified, helpful, title, body, gpt_status, gpt_reason, ben_analysis, paul_analysis, patrick_analysis, drew_analysis, rating, images, videos, url, variation, style) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"


# Iterate over the rows and insert them into the database
for row in rows:
    cur.execute(insert_query, row[:18])  # Assuming each row has 18 columns
    conn.commit()

# Close the cursor and the connection
cur.close()
conn.close()

